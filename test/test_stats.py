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
from __future__ import (absolute_import, division, print_function,
                        with_statement)

import json

from schematics.models import Model
from schematics.types import StringType

from tornado import gen
from tornado.testing import AsyncHTTPTestCase

import supercell.api as s
from supercell.environment import Environment
from supercell.environment import ScalesSupercellHandler


class SimpleMessage(Model):
    doc_id = StringType()
    message = StringType()


@s.provides(s.MediaType.ApplicationJson, default=True)
class MyHandler(s.RequestHandler):

    @s.latency
    @s.coroutine
    def get(self, *args, **kwargs):
        future = self._long_method()
        assert future.result() == 'TEST'
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))

    @s.latency
    @s.metered
    @gen.coroutine
    def _long_method(self):
        a = MyTestObject()
        assert a.do_something() == 'blah'
        raise s.Return('TEST')


class MyTestObject(object):

    @s.latency
    @s.metered
    def do_something(self):
        return 'blah'


class TestSupercellStats(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_handler('/teststats', MyHandler)
        env.add_handler('/_system/stats(.*)', ScalesSupercellHandler)
        return env.get_application()

    def test_simple_stats(self):
        # call the handler first so that something is recorded
        response = self.fetch('/teststats')
        self.assertEqual(response.code, 200)
        self.assertEqual('{"doc_id": "test123", "message": "A test"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

        # now check if we get something back in the stats
        response = self.fetch('/_system/stats')
        self.assertEqual(response.code, 200)
        self.assertTrue(len(response.body) > 0)

        response = self.fetch('/_system/stats/teststats')
        self.assertEqual(response.code, 200)
        expected = '{"_long_method": {"count": 1, "unit":' + \
            ' "per second"}, "latency": {"_long_method": ' + \
            '{"count": 1}, "get":' + \
            ' {"count": 1}}}'
        self.assertEqual(expected, json.dumps(json.loads(
            response.body.decode('utf8')), sort_keys=True))

        response = self.fetch('/teststats')
        self.assertEqual(response.code, 200)

        response = self.fetch('/_system/stats/teststats')
        self.assertEqual(response.code, 200)
        result = json.loads(response.body.decode('utf8'))
        self.assertEqual(result['latency']['get']['count'], 2)
        self.assertEqual(result['latency']['_long_method']['count'], 2)
        self.assertEqual(result['_long_method']['count'], 2)

        response = self.fetch('/_system/stats/')
        self.assertEqual(response.code, 200)
        result = json.loads(response.body.decode('utf8'))
        self.assertEqual(result['_internal']['test_stats']['MyTestObject']
                         ['do_something']['count'], 2)
        self.assertEqual(result['_internal']['test_stats']['MyTestObject']
                         ['latency']['do_something']['count'], 2)
