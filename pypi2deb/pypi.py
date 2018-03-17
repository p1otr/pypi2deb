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

import atexit
import logging
import asyncio
from os import environ
from os.path import exists, join
from xmlrpc.client import ServerProxy
# from aioxmlrpc.client import ServerProxy  # TODO: package it in Debian
import aiohttp

from pypi2deb.decorators import cache
from pypi2deb.tools import pkg_name, execute

PYPI_JSON_URL = environ.get('PYPI_JSON_URL', 'https://pypi.python.org/pypi/')
PYPI_XMLRPC_URL = environ.get('PYPI_XMLRPC_URL', 'https://pypi.python.org/pypi')
log = logging.getLogger('pypi2deb')


@asyncio.coroutine
def get_pypi_info(name, version=None):
    url = PYPI_JSON_URL + '/' + name
    if version:
        url += '/' + version
    url += '/json'
    session = None
    try:
        session = aiohttp.ClientSession()
        response = yield from session.get(url)
    except Exception as err:
        log.error('invalid project name: {} ({})'.format(name, err))
    else:
        try:
            result = yield from response.json()
        except Exception as err:
            log.warn('cannot download %s %s details from PyPI: %r', name, version, err)
            return
        return result
    finally:
        session is not None and session.close()


def parse_pypi_info(data):
    if not data:
        return {}

    for key, value in list(data['info'].items()):
        if value == 'UNKNOWN':
            data['info'][key] = ''

    info = data['info']
    result = {
        'name': info['name'],
        'version': info['version'],
        'description': info['description'].replace('\r\n', '\n'),
        'license_name': info['license'],
        'author': '{author} <{author_email}>'.format(**info),
        'homepage': info['home_page'],
    }
    if 'requires' in info:  # see f.e. qutebrowser
        result['requires'] = info['requires']

    summary = info['summary'].replace('  ', ' ')
    unwanted_prefixes = {'a', 'an', 'the', 'is', result['name'].lower()}
    while True:
        if ' ' not in summary:
            break
        prefix, rest = summary.split(maxsplit=1)
        if prefix.lower() in unwanted_prefixes:
            summary = rest
        else:
            break
    if summary.endswith('.'):
        summary = summary[:-1]
    result['summary'] = summary

    classifiers = data['info']['classifiers']
    result['interpreters'] = set()
    for i in classifiers:
        if i.startswith('Programming Language :: Python :: 3'):
            result['interpreters'].add('python3')
        elif i.startswith('Programming Language :: Python :: 2'):
            result['interpreters'].add('python')
    if 'Programming Language :: Python :: Implementation :: PyPy' in classifiers:
        result['interpreters'].add('pypy')
    if not result['interpreters']:
        # assume it's Python 2.X only
        result['interpreters'].add('python')

    return result


def parse_pkg_info(fpath):
    """Parse PKG-INFO file"""
    raise NotImplementedError()  # FIXME

@asyncio.coroutine
def download(name, version=None, destdir='.'):
    details = yield from get_pypi_info(name, version)
    if not details:
        raise Exception('cannot get PyPI project details for {}'.format(name))

    if not version:
        version = details['info']['version']

    release = details['releases'].get(version, {})
    if not release:
        log.debug('missing release of %s %s on PyPI', name, version)
        raise Exception('missing release')
    try:
        release = next((i for i in release if i['python_version'] == 'source'))
    except StopIteration:
        release = None

    if not release:
        raise Exception('source package not available on PyPI')

    orig_ext = ext = release['filename'].replace('{}-{}.'.format(name, version), '')
    if ext not in {'tar.gz', 'tar.bz2', 'tar.xz'}:
        ext = 'tar.xz'

    fname = '{}_{}.orig.{}'.format(pkg_name(name), version, ext)

    fpath = join(destdir, fname)
    if exists(fpath):
        return fname

    session = None
    try:
        session = aiohttp.ClientSession()
        response = yield from session.get(release['url'])
        with open(fpath if ext == orig_ext else join(destdir, release['filename']), 'wb') as fp:
            data = yield from response.read()
            fp.write(data)
    finally:
        session is not None and session.close()

    if orig_ext != ext:
        cmd = ['mk-origtargz', '--rename', '--compression', 'xz',
               '--package', pkg_name(details['info']['name']), '--version', version,
               '--directory', destdir,
               '--repack', join(destdir, release['filename'])]
        # TODO: add --copyright-file if overriden copyright file is available
        yield from execute(cmd)

    return fname


@cache()
def list_packages(classifiers=None):
    client = ServerProxy(PYPI_XMLRPC_URL)
    if not classifiers:
        # packages = yield from client.list_packages()
        packages = client.list_packages()
        packages = dict.fromkeys(packages)
    else:
        # packages = yield from client.browse(classifiers)
        packages = client.browse(classifiers)
        # browse returns all versions, use the latest one only
        # TODO: use LooseVersion
        packages = dict(sorted(packages))
    return packages
