# vim: set fileencoding=utf-8 :
#
# Copyright (c) 2014 Daniel Truemper <truemped at googlemail.com>
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

from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase as TornadoAsyncHTTPTestCase

import pytest


class AsyncHTTPTestCase(TornadoAsyncHTTPTestCase):

    ARGV = []
    SERVICE = None

    @pytest.fixture(autouse=True)
    def set_commandline(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['pytest'] + self.ARGV)

    def get_new_ioloop(self):
        return IOLoop.current\
            ()

    def get_app(self):
        service = self.SERVICE()
        service.initialize_logging()
        return service.get_app()
