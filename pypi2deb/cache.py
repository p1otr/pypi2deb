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

__all__ = ['load', 'dump']

try:
    import msgpack as _serializer
    NAMESPACE = 'P2D:'
except ImportError:
    NAMESPACE = 'P2D-j:'
    try:
        import simplejson as _serializer
    except ImportError:
        import json as _serializer
try:
    import redis
except ImportError:
    conn = None
else:
    conn = redis.Redis()
    try:
        conn.ping()
    except redis.ConnectionError:
        conn = None
if not conn:

    class _FallbackCache(dict):
        def setex(self, key, data, ttl=None):
            self[key] = data

        def get(self, key, default=None):
            return super(_FallbackCache, self).get(key, default)

    conn = _FallbackCache()


log = logging.getLogger('pypi2deb')


def load(key, default=None):
    result = conn.get(NAMESPACE + key)
    if result is None:
        return default
    try:
        return _serializer.loads(result, encoding='utf-8')
    except Exception as err:
        exc_info = log.level <= logging.DEBUG
        log.warn('cannot load cache (%s): %s', key, err, exc_info=exc_info)
        return default


def dump(key, data, ttl=3600):
    exc_info = log.level <= logging.DEBUG
    try:
        data = _serializer.dumps(data)
    except Exception as err:
        log.warn('cannot serialize cache (%s): %s', key, err, exc_info=exc_info)
        return
    try:
        conn.setex(NAMESPACE + key, data, ttl)
    except Exception as err:
        log.warn('cannot dump cache (%s): %s', key, err, exc_info=exc_info)
