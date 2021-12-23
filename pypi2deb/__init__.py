# Copyright © 2015-2018 Piotr Ożarowski <piotr@debian.org>
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

import sys
from os import environ
from os.path import join, dirname, abspath

TEMPLATES_PATH = environ.get('PYPI2DEB_TEMPLATES_PATH',
                             abspath(join(dirname(__file__), '..', 'templates')))
OVERRIDES_PATH = environ.get('PYPI2DEB_OVERRIDES_PATH',
                             abspath(join(dirname(__file__), '..', 'overrides')))
PROFILES_PATH = environ.get('PYPI2DEB_PROFILES_PATH',
                            abspath(join(dirname(__file__), '..', 'profiles')))
VERSION = '2.20211223-morph'
# Add path to dh-python's private library
# (yeah, it's not stable enough to make it public one, fortunatly
# author of pypi2deb and dh-python know each other ;)
sys.path.append('/usr/share/dh-python/')
