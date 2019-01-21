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

from tornado.testing import AsyncHTTPTestCase

from supercell.health import SystemHealthCheck
import supercell.api as s
from supercell.environment import Environment


class TestBasicHealthChecks(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_handler('/_system/check', SystemHealthCheck)
        return env.get_application()

    def test_simple_check(self):
        response = self.fetch('/_system/check')
        self.assertEqual(response.code, 200)
        self.assertEqual(
            '{"code": "OK", "message": "API running", "ok": true}',
            json.dumps(json.loads(response.body.decode('utf8')),
                       sort_keys=True))


class SimpleHealthCheckExample(s.RequestHandler):

    @s.coroutine
    def get(self):
        raise s.HealthCheckWarning()


class SimpleErrorCheckExample(s.RequestHandler):

    @s.coroutine
    def get(self):
        raise s.HealthCheckError()


class TestCustomHealthCheck(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_health_check('test', SimpleHealthCheckExample)
        env.add_health_check('error', SimpleErrorCheckExample)
        return env.get_application()

    def test_simple_warning(self):
        response = self.fetch('/_system/check/test')
        self.assertEqual(response.code, 500)
        self.assertEqual('{"code": "WARNING", "error": true}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

    def test_simple_error(self):
        response = self.fetch('/_system/check/error')
        self.assertEqual(response.code, 500)
        self.assertEqual('{"code": "ERROR", "error": true}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))
