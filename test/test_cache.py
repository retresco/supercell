# vim: set fileencoding=utf-8 :
#
# Copyright (c) 2013 Daniel Truemper <truemped at googlemail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
from datetime import datetime, timedelta
import json

from schematics.models import Model
from schematics.types import StringType

from tornado import gen
from tornado.testing import AsyncHTTPTestCase

import supercell.api as s
from supercell.api import (RequestHandler, provides, CacheConfig)
from supercell.environment import Environment


class SimpleMessage(Model):
    doc_id = StringType()
    message = StringType()


@provides(s.MediaType.ApplicationJson, default=True)
class MyHandler(RequestHandler):

    @s.coroutine
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


@provides(s.MediaType.ApplicationJson, default=True)
class MyExtremeCachingHandler(RequestHandler):

    @s.coroutine
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


@provides(s.MediaType.ApplicationJson, default=True)
class MyPrivateCaching(RequestHandler):

    @s.coroutine
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


@provides(s.MediaType.ApplicationJson, default=True)
class CachingWithYielding(RequestHandler):

    @s.coroutine
    def get(self, *args, **kwargs):
        result = yield self.a_coroutine()
        assert result, 'yes'
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))

    @gen.coroutine
    def a_coroutine(self):
        raise s.Return('yes')


@provides(s.MediaType.ApplicationJson, default=True)
class CachingWithoutDecorator(RequestHandler):

    @s.coroutine
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


class TestCacheDecorator(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_handler(r'/', MyHandler,
                        cache=CacheConfig(timedelta(minutes=10)))
        env.add_handler(r'/cache', MyExtremeCachingHandler,
                        cache=CacheConfig(timedelta(minutes=10),
                                          s_max_age=timedelta(minutes=10),
                                          public=True, must_revalidate=True,
                                          proxy_revalidate=True),
                        expires=timedelta(minutes=15))
        env.add_handler(r'/private', MyPrivateCaching,
                        cache=CacheConfig(timedelta(seconds=10),
                                          s_max_age=timedelta(seconds=0),
                                          private=True, no_store=True))
        env.add_handler(r'/nested_async', CachingWithYielding,
                        cache=CacheConfig(timedelta(seconds=10)))
        return env.get_application()

    def test_simple_timedelta(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)
        self.assertTrue('Cache-Control' in response.headers)
        self.assertEqual('max-age=600, must-revalidate',
                         response.headers['Cache-Control'])

    def test_extreme_cache(self):
        response = self.fetch('/cache')
        self.assertEqual(response.code, 200)
        self.assertTrue('Cache-Control' in response.headers)
        self.assertEqual('max-age=600, s-max-age=600, public, ' +
                         'must-revalidate, proxy-revalidate',
                         response.headers['Cache-Control'])

        self.assertTrue('Expires' in response.headers)
        ts = datetime.strptime(response.headers['Expires'],
                               '%a, %d %b %Y %H:%M:%S %Z')
        self.assertTrue(ts > datetime.now())

    def test_private_cache(self):
        response = self.fetch('/private')
        self.assertEqual(response.code, 200)
        self.assertTrue('Cache-Control' in response.headers)
        self.assertEqual('max-age=10, private, no-store, must-revalidate',
                         response.headers['Cache-Control'])

    def test_caching_with_yielding(self):
        response = self.fetch('/nested_async')
        self.assertEqual(response.code, 200)
        self.assertTrue('Cache-Control' in response.headers)
        self.assertEqual('max-age=10, must-revalidate',
                         response.headers['Cache-Control'])
        self.assertEqual('{"doc_id": "test123", "message": "A test"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))
