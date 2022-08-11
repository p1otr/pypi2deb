# Copyright © 2021 Sandro Tosi <morph@debian.org>
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

# PyGithub doesnt support (yet) asyncio, and there's only a prototype of a github
# client supporting it, so we're gonna do it the old way

import logging
import asyncio
from os.path import join, exists

import aiohttp
from github import Github
from github.GithubException import UnknownObjectException

log = logging.getLogger('pypi2deb')


@asyncio.coroutine
def github_download(name, github_url, version=None, destdir='.'):
    g = Github()
    repo_name = github_url.replace('https://github.com/', '').rstrip('/')
    log.debug(f"Calling github get_repo with arg {repo_name}")
    repo = g.get_repo(repo_name)

    if not name:
        name = repo.name

    try:
        tag_name = repo.get_latest_release().tag_name
    except UnknownObjectException:
        # Some projects do not use Github Releases, check the latest tag instead
        tag_name = repo.get_tags()[0].name

    if not version:
        # TODO: are there other special cases? vx.y.z tag gets rewritten as x.y.z
        version = tag_name.lstrip('v')

    # cant use this for now, chk https://github.com/PyGithub/PyGithub/issues/1871
    # download_url = latest_release.tarball_url
    # so let's "forge" the right URL here
    download_url = f"{github_url}/archive/{tag_name}.tar.gz"

    fname = f'{name}_{version}.orig.tar.gz'

    fpath = join(destdir, fname)
    if exists(fpath):
        return fname

    session = None
    try:
        session = aiohttp.ClientSession()
        response = yield from session.get(download_url)
        with open(fpath, 'ba') as fp:
            data = yield from response.read()
            fp.write(data)
    finally:
        if session is not None:
            yield from session.close()

    return fname
