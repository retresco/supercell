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

import sys
if sys.version_info > (2, 7):
    from unittest import TestCase
    from unittest import skipIf
else:
    from unittest2 import TestCase
    from unittest2 import skipIf

import tornado
from tornado import httputil
from tornado.web import Application, RequestHandler

from supercell.environment import Environment


class EnvironmentTest(TestCase):

    def test_simple_app_creation(self):
        env = Environment()
        app = env.get_application()
        self.assertIsInstance(app, Application)
        if tornado.version < '4.5':
            self.assertEqual(len(app.handlers), 2)
        else:
            self.assertEqual(len(app.default_router.rules), 3)

    def test_config_file_paths(self):
        env = Environment()
        self.assertEqual(len(env.config_file_paths), 0)

    @skipIf(tornado.version < '4.5', 'test requires tornado.routing')
    def test_add_handler(self):
        env = Environment()
        self.assertEqual(len(env._handlers), 0)

        class MyHandler(RequestHandler):
            def get(self):
                self.write({'ok': True})

        env.add_handler('/test', MyHandler, {})

        self.assertEqual(len(env._handlers), 1)

        app = env.get_application()

        request = httputil.HTTPServerRequest(uri='/test')
        handler_delegate = app.default_router.find_handler(request)
        self.assertIsNotNone(handler_delegate)
        self.assertEqual(handler_delegate.handler_class, MyHandler)

    def test_managed_object_access(self):
        env = Environment()

        managed = object()
        env.add_managed_object('i_am_managed', managed)
        self.assertEqual(managed, env.i_am_managed)

    def test_no_overwriting_of_managed_objects(self):
        env = Environment()
        managed = object()
        env.add_managed_object('i_am_managed', managed)

        self.assertEqual(managed, env.i_am_managed)
        with self.assertRaises(AssertionError):
            env.add_managed_object('i_am_managed', object())

    def test_finalizing(self):
        env = Environment()
        managed = object()
        env.add_managed_object('i_am_managed', managed)
        env._finalize()

        with self.assertRaises(AssertionError):
            env.add_managed_object('another_managed', object())
