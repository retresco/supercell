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
else:
    from unittest2 import TestCase

import socket

import mock
import pytest

from schematics.models import Model
from schematics.types import StringType
import tornado.options
from tornado.testing import AsyncHTTPTestCase

import supercell.api as s
from supercell.environment import Environment


class SimpleModel(Model):
    msg = StringType()


@s.provides(s.MediaType.ApplicationJson)
@s.consumes(s.MediaType.ApplicationJson, SimpleModel)
class MyHandler(s.RequestHandler):

    @s.coroutine
    def get(self):
        self.logger.info('Holy moly')
        self.logger.info('That worked')
        raise s.Return(SimpleModel({"msg": 'Holy moly'}))

    @s.coroutine
    def post(self, doc_id, model=None):
        self.logger.info('Holy moly')
        raise s.Return(SimpleModel({"msg": 'Holy moly'}))
        assert isinstance(self.environment, Environment)
        assert isinstance(self.config, tornado.options.options)
        raise s.OkCreated({'docid': 123})


@s.provides(s.MediaType.ApplicationJson, default=True)
class MyHandlerThrowingExceptions(s.RequestHandler):

    @s.coroutine
    def get(self):
        self.logger.info('Starting request with unhandled exception')
        raise Exception()


class MyService(s.Service):

    def bootstrap(self):
        self.environment.config_file_paths.append('test/')

    def run(self):
        self.environment.add_handler('/test', MyHandler, {})
        self.environment.add_handler('/test/(\d+)', MyHandler, {})
        self.environment.add_handler('/exception', MyHandlerThrowingExceptions,
                                     {})


class ServiceTest(TestCase):

    @pytest.fixture(autouse=True)
    def empty_commandline(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [])

    def test_environment_creation(self):
        service = s.Service()
        env = service.environment
        self.assertIsInstance(env, Environment)

    def test_logging_initialization(self):
        service = s.Service()
        env = service.environment
        env.config_file_paths.append('test/')

        service.initialize_logging()

    @mock.patch('tornado.ioloop.IOLoop.current')
    def test_main_method(self, ioloop_instance_mock):
        service = MyService()
        service.main()

        ioloop_instance_mock.assert_called()
        ioloop_instance_mock().start.assert_called()
        ioloop_instance_mock().add_handler.assert_called()
        service.shutdown()


    @mock.patch('tornado.ioloop.IOLoop.current')
    @mock.patch('socket.fromfd')
    def test_startup_with_socket_fd(self, socket_fromfd_mock,
                                    ioloop_instance_mock):

        service = MyService()
        service.config.socketfd = '123'

        service.main()

        expected = [mock.call(), mock.call().add_handler(mock.ANY, mock.ANY,
                                                         mock.ANY),
                    mock.call(), mock.call().start()]
        assert expected == ioloop_instance_mock.mock_calls

        assert (mock.call(123, socket.AF_INET, socket.SOCK_STREAM)
                in socket_fromfd_mock.mock_calls)
        service.shutdown()


    @mock.patch('tornado.ioloop.IOLoop.current')
    def test_graceful_shutdown_pending_callbacks(self, ioloop_instance_mock):
        service = MyService()
        service.main()

        expected = [mock.call(), mock.call().add_handler(mock.ANY, mock.ANY,
                                                         mock.ANY),
                    mock.call(), mock.call().start()]
        assert expected == ioloop_instance_mock.mock_calls

        service.shutdown()

        if sys.version_info < (3,):
            expected.extend([mock.call(), mock.call().remove_handler(mock.ANY),
                             mock.call()._callbacks.__nonzero__(),
                             mock.call()._callbacks.__nonzero__(),
                             mock.call().add_timeout(mock.ANY, mock.ANY)])
        else:
            expected.extend([mock.call(), mock.call().remove_handler(mock.ANY),
                             mock.call()._callbacks.__bool__(),
                             mock.call()._callbacks.__bool__(),
                             mock.call().add_timeout(mock.ANY, mock.ANY)])

        assert expected == ioloop_instance_mock.mock_calls

    @mock.patch('tornado.ioloop.IOLoop.current')
    def test_graceful_final_shutdown(self, ioloop_instance_mock):
        service = MyService()
        service.main()
        service.config.max_grace_seconds = -10

        expected = [mock.call(), mock.call().add_handler(mock.ANY, mock.ANY,
                                                         mock.ANY),
                    mock.call(), mock.call().start()]
        assert expected == ioloop_instance_mock.mock_calls

        service.shutdown()

        expected.extend([mock.call(), mock.call().remove_handler(mock.ANY),
                         mock.call().stop()])
        assert expected == ioloop_instance_mock.mock_calls

        service.config.max_grace_seconds = 3
        service.shutdown()


class ApplicationIntegrationTest(AsyncHTTPTestCase):

    @pytest.fixture(autouse=True)
    def set_commandline(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['pytest'])

    def get_app(self):
        service = MyService()
        service.initialize_logging()
        return service.get_app()

    def test_simple_get(self):
        response = self.fetch('/test', headers={'Accept':
                                                s.MediaType.ApplicationJson})
        self.assertEqual(200, response.code)
        self.assertEqual('{"msg": "Holy moly"}', response.body.decode('utf8'))

    def test_get_with_exception(self):
        response = self.fetch('/exception')
        self.assertEqual(500, response.code)


@pytest.mark.parametrize('option_name', [
    '--show_config',
    '--show_config_name',
    '--show_config_file_order'
])
def test_system_exit_after_showing_config(option_name):
    with mock.patch('sys.argv', ['', option_name]):
        service = s.Service()
        with pytest.raises(SystemExit):
            service.get_app()


@pytest.fixture
def test_env_var(monkeypatch):
    monkeypatch.setenv("TEST", "envvalue")


def test_config_parsing(test_env_var):
    service = s.Service()
    env = service.environment
    env.config_file_paths.append('test/')
    tornado.options.define('test', default='default')
    service.parse_config_files()

    from tornado.options import options
    assert 'filevalue' == options.test

    service.parse_environment_variables(options)
    assert 'envvalue' == options.test
