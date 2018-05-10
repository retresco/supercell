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

import pytest

from tornado.testing import AsyncHTTPTestCase

from supercell.api import async
from supercell.api import provides
from supercell.api import RequestHandler
from supercell.api import Return
from supercell.api import Service


@provides('application/json', default=True)
class MyHandler(RequestHandler):

    @async
    def get(self):
        raise Return({"this": "is not returned"})


class MyService(Service):
    def run(self):
        env = self.environment
        env.add_handler('/test', MyHandler, {})


class ApplicationIntegrationTest(AsyncHTTPTestCase):

    @pytest.fixture(autouse=True)
    def empty_commandline(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [])

    def get_app(self):
        service = MyService()
        service.initialize_logging()
        return service.get_app()

    def test_that_returning_non_model_is_an_error(self):
        response = self.fetch('/test')
        self.assertEqual(500, response.code)
