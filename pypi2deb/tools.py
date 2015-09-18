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

import asyncio
import logging
import os
import re
import tarfile
from datetime import datetime
from os.path import exists, join
from shlex import split
from pypi2deb.decorators import cache
from dhpython.pydist import load, safe_name


FILENAME_RE = re.compile(r'''
    (?:.*/)?
    (?P<name>[a-zA-Z-].*)
    [-_]
    (?P<version>[0-9][A-Za-z0-9\-.+]*?)
    (?:
        \.
        (?:orig\.)?
        (?P<extension>(?:tar(?:\.[a-z0-9]+)?)|(?:zip))
    )?$
''', re.VERBOSE)
log = logging.getLogger('pypi2deb')


def unpack(fpath, destdir='.', dname=None):
    if dname:
        dst_dpath = join(destdir, dname)
        if exists(dst_dpath):
            log.debug('{} already exists, no need to unpack'.format(dname))
            return dst_dpath
    else:
        dst_dpath = None

    fname = fpath.rsplit('/', 1)[-1]
    if '.tar.' in fname:
        with tarfile.open(fpath, 'r') as tar:
            members = []
            for memb in tar.getmembers():
                if memb.name.startswith('/') or '../' in memb.name:
                    log.warn('skipping invalid file name: %s', memb.name)
                    continue
                members.append(memb)

            dirname = members[0].name
            if not members[0].isdir():
                destdir = dst_dpath = join(destdir, dname or 'extracted')
                dirname = dname = None
                if exists(destdir):
                    log.debug('{} already exists, no need to unpack'.format(destdir))
                    return destdir
            elif not dst_dpath:
                dst_dpath = join(destdir, dirname)

            tar.extractall(destdir, members)
        if dname and dname != dirname:
            os.rename(join(destdir, dirname), dst_dpath)
        return dst_dpath


def parse_filename(name):
    match = FILENAME_RE.match(name)
    return match.groupdict() if match else {}


@asyncio.coroutine
def execute(command, cwd=None, env=None, log_output=None):
    """Execute external shell commad.

    :param cdw: currennt working directory
    :param env: environment
    :param log_output:
        * opened log file or path to this file, or
        * None if output should be redirectored to stdout/stderr
    """
    env = env or os.environ
    close = False
    if log_output:
        if isinstance(log_output, str):
            close = True
            log_output = open(log_output, 'a', encoding='utf-8')
        log_output.write('\n# command executed on {}'.format(datetime.now().isoformat()))
        log_output.write('\n$ {}\n'.format(command))
        log_output.flush()

    if isinstance(command, str):
        command = split(command)
    log.debug('invoking: %s in %s', command, cwd)

    create = asyncio.create_subprocess_exec(*command, stdout=log_output, stderr=log_output,
                                            cwd=cwd, env=env)
    proc = yield from create
    yield from proc.wait()
    close and log_output.close()

    return proc.returncode


def pkg_name(name):
    names = _load_package_names()
    name = safe_name(name).lower()
    if name in names:
        return names[name]
    result = name.lower().replace('-python', '').replace('python-', '')
    if result.endswith('.py'):
        result = result[:-3]
    result = re.sub('[^a-z0-9.-]', '-', result)
    return result


@cache()
def _load_package_names():
    result = {}
    try:
        data = load('cpython3')
    except Exception as err:
        log.warn('cannot load pydist names: %s', err)
        data = {}
    else:
        for key, details in data.items():
            result[key.lower()] = details[0]['dependency'].replace('python3-', '')
    try:
        data2 = load('cpython2')
    except Exception as err:
        log.warn('cannot load pydist names: %s', err)
        data2 = {}
    else:
        for key, details in data2.items():
            key = key.lower()
            if key not in result:
                result[key] = details[0]['dependency'].replace('python-', '')
    return result
