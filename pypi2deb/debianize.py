# Copyright © 2015 Piotr Ożarowski <piotr@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from configparser import ConfigParser
from datetime import datetime
from os import access, chmod, listdir, makedirs, walk, X_OK
from os.path import abspath, exists, isdir, join
from shutil import copy

from pypi2deb import VERSION, OVERRIDES_PATH, PROFILES_PATH, TEMPLATES_PATH
from pypi2deb.tools import execute

from jinja2 import Environment, FileSystemLoader
from debian.changelog import Changelog, Version, get_maintainer
try:
    from simplejson import load, dump
except ImportError:
    from json import load, dump

from dhpython import PKG_PREFIX_MAP
from dhpython.pydist import guess_dependency, parse_pydep


log = logging.getLogger('pypi2deb')
SPHINX_DIR = {'docs', 'doc', 'doc/build'}
INTERPRETER_MAP = {value: key for key, value in PKG_PREFIX_MAP.items()}
VERSIONED_I_MAP = {'python': 'python2'}
DESC_STOP_KEYWORDS = {'changelog', 'changes', 'license', 'requirements',
                      'installation'}


def _copy_static_files(src_dir, debian_dir):
    """Copy static templates/overrides from source to destination"""
    for root, dirs, file_names in walk(src_dir):
        for fn in file_names:
            if fn.endswith(('.tpl', '.swp')):
                continue
            dst_dir = root.replace(src_dir, debian_dir)
            if not exists(dst_dir):
                makedirs(dst_dir)
            if not exists(join(dst_dir, fn)):
                copy(join(root, fn), join(dst_dir, fn))


def debianize(dpath, ctx, profile=None):
    update_ctx(dpath, ctx)

    setupcfg_fpath = join(dpath, 'setup.cfg')
    if exists(setupcfg_fpath):
        upstream_cfg = ConfigParser()
        upstream_cfg.read(setupcfg_fpath)
        if 'py2dsp' in upstream_cfg:
            ctx.update(upstream_cfg['py2dsp'].items())

    override_paths = [TEMPLATES_PATH]

    # profile overrides
    if profile:
        if isdir(profile):  # --profile a_dir
            override_paths.append(profile)
        elif exists(profile):  # --profile a_file
            with open(profile) as fp:
                ctx.update(load(fp))
        else:  # --profile name
            profile_dpath = join(PROFILES_PATH, profile)
            if isdir(profile_dpath):
                override_paths.append(profile_dpath)

    # package specific overrides... in global overrides dir
    o_dpath = join(OVERRIDES_PATH, ctx['name'].lower())
    isdir(o_dpath) and override_paths.append(o_dpath)
    # ... in local ./overrides
    o_dpath = join('overrides', ctx['name'].lower())
    isdir(o_dpath) and override_paths.append(o_dpath)

    # handle overrides
    debian_dir = join(dpath, 'debian')
    for o_dpath in override_paths:
        fpath = join(o_dpath, 'ctx.json')
        if exists(fpath):
            with open(fpath) as fp:
                ctx.update(load(fp))
        # invoke pre hooks
        fpath = abspath(join(o_dpath, 'hooks', 'pre'))
        if exists(fpath) and access(fpath, X_OK):
            _dump_ctx(ctx)
            code = yield from execute([fpath, ctx['src_name'],
                                       ctx['version'], ctx['debian_revision']],
                                      cwd=dpath)
            if code != 0:
                raise Exception("pre hook for %s failed with %d return code" % (
                                ctx['name'], code))
    for o_dpath in reversed(override_paths):
        # copy static files
        deb_dpath = join(o_dpath, 'debian')
        if isdir(deb_dpath):
            _copy_static_files(deb_dpath, debian_dir)

    for key in ('vcs_src', 'vcs_browser', 'uploaders'):
        if key in ctx:
            ctx[key] = ctx[key].format(**ctx)
    ctx['debian_version'] = "{}-{}".format(ctx['version'], ctx['debian_revision'])

    # Jinja setup: set templates directories
    templates_dir = [dpath]  # use existing dir as a template dir as well
    templates_dir.extend(override_paths)
    templates_dir.append(TEMPLATES_PATH)
    env = Environment(loader=FileSystemLoader(templates_dir))

    # render debian dir files (note that order matters)
    docs(dpath, ctx, env)
    control(dpath, ctx, env)
    rules(dpath, ctx, env)
    chmod(join(dpath, 'debian', 'rules'), 0o755)
    initial_release = yield from changelog(dpath, ctx, env)
    if initial_release:
        itp_mail(dpath, ctx, env)
    copyright(dpath, ctx, env)
    watch(dpath, ctx, env)
    clean(dpath, ctx, env)

    # invoke post hooks
    for o_dpath in override_paths:
        fpath = join(o_dpath, 'hooks', 'post')
        if exists(fpath) and access(fpath, X_OK):
            _dump_ctx(ctx)
            code = yield from execute([fpath, ctx['src_name'],
                                       ctx['version'], ctx['debian_revision']],
                                      cwd=dpath)
            if code != 0:
                raise Exception("post hook for %s failed with %d return code" % (
                                ctx['name'], code))


def update_ctx(dpath, ctx):
    ctx.setdefault('exports', {})
    ctx.setdefault('build_depends', set())
    maintainer, email = get_maintainer()
    ctx['creator'] = '{} <{}>'.format(maintainer, email)
    if 'maintainer' not in ctx:
        ctx['maintainer'] = '{} <{}>'.format(maintainer, email)
    if 'debian_revision' not in ctx:
        ctx['debian_revision'] = '0~pypi2deb'

    ctx['binary_arch'] = 'all'
    ctx.setdefault('clean_files', set())
    for root, dirs, file_names in walk(dpath):
        if any(fname.endswith(('.c', '.cpp', '.pyx')) for fname in file_names):
            ctx['binary_arch'] = 'any'

            for fname in file_names:
                if fname.endswith('.pyx'):
                    if 'python' in ctx['interpreters']:
                        ctx['build_depends'].add('cython')
                    if 'python3' in ctx['interpreters']:
                        ctx['build_depends'].add('cython3')
                    for ext in ('c', 'cpp'):
                        fname_c = fname[:-3] + ext
                        if fname_c in file_names:
                            ctx['clean_files'].add(join(root.replace(dpath, '.'), fname_c))


def _dump_ctx(ctx):
    """dump ctx in JSON format so that hooks can use it"""
    try:
        fpath = join(ctx['root'], '{src_name}_{version}-{debian_revision}.ctx'.format(**ctx))
        serializable_ctx = {key: (value if not isinstance(value, set) else tuple(value))
                            for (key, value) in ctx.items()}
        with open(fpath, 'w') as fp:
            dump(serializable_ctx, fp, indent=' ')
    except Exception:
        log.debug('cannot dump ctx', exc_info=True)


def docs(dpath, ctx, env):
    docs = ctx.setdefault('docs', {})
    for path in SPHINX_DIR:
        if exists(join(dpath, path, 'Makefile')) and exists(join(dpath, path, 'conf.py')):
            docs['sphinx_dir'] = path
            ctx['build_depends'].add('python3-sphinx')
            docs.setdefault('files', []).append('.pybuild/docs/*')
    for fn in listdir(dpath):
        if fn.lower().startswith('readme'):
            docs.setdefault('files', []).append(fn)
        if fn.lower() == 'examples':
            docs['examples_dir'] = fn
    if docs:
        if 'sphinx_dir' in docs:
            # i.e. we have binary packages with docs
            docs_pkg = 'python-{}-doc'
        elif 'python3' in ctx['interpreters']:
            docs_pkg = 'python3-{}'
        else:
            docs_pkg = 'python-{}'
        docs_pkg = docs_pkg.format(ctx['src_name'])
        if 'examples_dir' in docs:
            # TODO: should we extend this file only if it exists?
            with open(join(dpath, 'debian', docs_pkg + '.examples'), 'w') as fp:
                fp.write("{}/*\n".format(docs['examples_dir']))
        if 'files' in docs:
            # TODO: should we extend this file only if it exists?
            with open(join(dpath, 'debian', docs_pkg + '.docs'), 'w') as fp:
                for fn in docs['files']:
                    fp.write("{}\n".format(fn))


def _render_template(func):
    name = func.__name__

    def _template(dpath, ctx, env, *args, **kwargs):
        fpath = join(dpath, 'debian', name)
        if exists(fpath):
            log.debug('debian/%s already exist, skipping', name)
            return
        ctx = func(dpath, ctx, env, *args, **kwargs)
        tpl = env.get_template('debian/{}.tpl'.format(name))
        with open(fpath, 'w', encoding='utf-8') as fp:
            fp.write(tpl.render(ctx))
    return _template


@_render_template
def control(dpath, ctx, env):
    desc = []
    code_line = False
    first_line = True
    for line in ctx['description'].split('\n'):
        if first_line:
            if line.lower() == ctx['name'].lower():
                continue
            if not line.strip().replace('=', '').replace('-', '').replace('~', ''):
                continue
            first_line = False
        if not line.strip():
            desc.append(' .')
        else:
            if line.startswith(('* ', '>>> ', '... ', '.. ', '$ ')) \
               or code_line or line == '...':
                if line.startswith('>>> '):
                    # next line should get extra space char as well
                    code_line = True
                elif code_line:
                    code_line = False
                line = ' ' + line
            elif line.strip().lower() in DESC_STOP_KEYWORDS:
                break
            line = line.replace('\t', '    ')
            desc.append(' ' + line)
    for key, value in {
        'short_desc': ctx['summary'][:80],
        'long_desc': '\n'.join(desc),
    }.items():
        if key not in ctx:
            ctx[key] = value

    req = set()
    if 'requires' in ctx:
            for impl in ctx['interpreters']:
                impl = INTERPRETER_MAP.get(impl, impl)
                try:
                    dependency = guess_dependency(impl, line)
                    if dependency:
                        ctx['build_depends'].add(dependency)
                except Exception as err:
                    log.warn('cannot parse build dependency: %s', err)
    else:
        for i in listdir(dpath):
            if i.endswith('.egg-info') and exists(join(dpath, i, 'requires.txt')):
                req.add(join(dpath, i, 'requires.txt'))
            if i == 'requirements.txt':
                req.add(join(dpath, 'requirements.txt'))

        for fpath in req:
            for impl in ctx['interpreters']:
                impl = INTERPRETER_MAP.get(impl, impl)
                try:
                    for i in parse_pydep(impl, fpath):
                        ctx['build_depends'].add(i)
                except Exception as err:
                    log.warn('cannot parse build dependency: %s', err)

    if exists(join(dpath, 'setup.py')):
        with open(join(dpath, 'setup.py')) as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                if 'setuptools' in line:
                    for interpreter in ctx['interpreters']:
                        ctx['build_depends'].add('{}-setuptools'.format(interpreter))

    if 'python' in ctx['interpreters']:
        ctx['build_depends'].add(
            'python-all%s' % ('-dev' if ctx['binary_arch'] == 'any' else ''))
    if 'python3' in ctx['interpreters']:
        ctx['build_depends'].add(
            'python3-all%s' % ('-dev' if ctx['binary_arch'] == 'any' else ''))
    if 'pypy' in ctx['interpreters']:
        ctx['build_depends'].add('pypy')

    return ctx


@_render_template
def rules(dpath, ctx, env):
    ctx['with'] = ','.join(VERSIONED_I_MAP.get(i, i) for i in ctx['interpreters'])
    if ctx.get('docs', {}).get('sphinx_dir'):
        ctx['with'] += ',sphinxdoc'

    # if package install a script in /usr/bin/ - ship it only in python3-foo package
    if exists(join(dpath, 'setup.py')) and len(ctx['interpreters']) > 1:
        with open(join(dpath, 'setup.py')) as fp:
            for line in fp:
                if 'console_scripts' in line:
                    for interpreter in ctx['interpreters']:
                        if interpreter == 'python3':
                            continue
                        ipreter = VERSIONED_I_MAP.get(interpreter, interpreter)
                        ctx['exports']['PYBUILD_AFTER_INSTALL_{}'.format(ipreter)] = 'rm -rf {destdir}/usr/bin/'
                    break

    return ctx


def changelog(dpath, ctx, env):
    change = ctx.get('message', 'Autogenerated by py2dsp v{}'.format(VERSION))
    version = ctx['debian_version']
    distribution = ctx.get('distribution', 'UNRELEASED')

    fpath = join(dpath, 'debian', 'changelog')
    if exists(fpath):
        with open(fpath, encoding='utf-8') as fp:
            line = fp.readline()
            if ctx['version'] in line or 'UNRELEASED' in line:
                log.debug('changelog doesn\'t need an update')
                return
            else:
                yield from execute(['dch', '--force-distribution', '--distribution', distribution,
                                    '--newversion', version, '-m', change], cwd=dpath)
        return

    now = datetime.utcnow()
    changelog = Changelog()
    changelog.new_block(package=ctx['src_name'],
                        version=Version(version),
                        distributions=distribution,
                        urgency='low',
                        author=ctx['creator'],
                        date=now.strftime('%a, %d %b %Y %H:%M:%S +0000'))
    changelog.add_change('')
    changelog.add_change('  * {}'.format(change))
    changelog.add_change('')

    with open(fpath, 'w', encoding='utf-8') as fp:
        changelog.write_to_open_file(fp)
    return True


@_render_template
def copyright(dpath, ctx, env):
    if not ctx.get('deb_copyright'):
        ctx['deb_copyright'] = "{} © {}".format(datetime.now().year, ctx['creator'])
    if ctx['license_name'] == 'Apache 2':
        ctx['license_name'] = 'Apache2'
        ctx['license'] = ' See /usr/share/common-licenses/Apache-2.0'
    if not ctx.get('deb_license_name'):
        ctx['deb_license_name'] = ctx['license_name']
        ctx['deb_license'] = ctx.get('license', '')
    if not ctx.get('deb_license') and ctx['deb_license_name']:
        ctx['deb_license'] = ''
        fpath = '/usr/share/common-licenses/{}'.format(ctx['deb_license_name'])
        if exists(fpath):
            license = []
            with open(fpath, encoding='utf-8') as fp:
                for line in fp:
                    line = line.rstrip()
                    license.append(' {}'.format(line) if line else ' .')
            ctx['deb_license'] = '\n'.join(license)

    ctx.setdefault('copyright', '')

    if not ctx.get('license'):
        license = []
        for fn in listdir(dpath):
            if not fn.lower().startswith('license'):
                continue
            with open(join(dpath, fn), 'r') as fp:
                for line in fp:
                    line = line.rstrip()
                    if not line:
                        license.append(' .')
                    else:
                        license.append(' ' + line)
                        if not ctx['copyright'] and line.lower().startswith('copyright '):
                            ctx['copyright'] = line[10:]
            if license:
                ctx['license'] = '\n'.join(license)
            break
    if not ctx.get('copyright'):
        ctx['copyright'] = ctx['author']
    return ctx


@_render_template
def watch(dpath, ctx, env):
    return ctx


def itp_mail(dpath, ctx, env):
    fpath = join(ctx['root'], '{src_name}_{version}-{debian_revision}.mail'.format(**ctx))
    if exists(fpath):
        return
    tpl = env.get_template('itp.mail')
    with open(fpath, 'w', encoding='utf-8') as fp:
        fp.write(tpl.render(ctx))


def clean(dpath, ctx, env):
    old = set()
    fpath = join(dpath, 'debian', 'clean')
    if exists(fpath):
        with open(fpath) as fp:
            for line in fp:
                old.add(line.strip())

    new = set()
    for i in ctx['clean_files']:
        if i not in old:
            new.add(i)

    if new:
        with open(fpath, 'a') as fp:
            for fn in new:
                fp.write("\n{}".format(fn))
