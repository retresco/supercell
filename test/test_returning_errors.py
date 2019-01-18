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
import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import HTTPError

from schematics.models import Model
from schematics.types import BooleanType, StringType

from supercell.api import coroutine
from supercell.api import provides
from supercell.api import consumes
from supercell.api import MediaType
from supercell.api import RequestHandler
from supercell.api import Return
from supercell.api import Service
from supercell.api import Error


@provides('text/html')
@provides('application/json', default=True)
@consumes(MediaType.ApplicationJson, object)
class MySimpleHandler(RequestHandler):
    @coroutine
    def get(self):
        raise Return({"this": "is not returned"})

    @coroutine
    def post(self):
        raise Return({"this": "is not returned"})


class SimpleModel(Model):
    doc_id = StringType(required=True)
    doc_bool = BooleanType(required=True)


@provides(MediaType.TextHtml)
@provides(MediaType.ApplicationJson, default=True)
@consumes(MediaType.ApplicationJson, SimpleModel)
class MyModelHandler(RequestHandler):
    @coroutine
    def get(self, model, **kwargs):
        invalid_model = SimpleModel({'doc_id': 'id'})
        raise Return(invalid_model)

    @coroutine
    def post(self, model, **kwargs):
        invalid_model = SimpleModel({'doc_id': 'id'})
        raise Return(invalid_model)


@provides(MediaType.TextHtml)
@provides(MediaType.ApplicationJson, default=True)
@consumes(MediaType.ApplicationJson, SimpleModel)
class MyErrorHandler(RequestHandler):
    @coroutine
    def get(self, *args, **kwargs):
        raise Error(406, additional={'message': 'My own error', 'code': 406})

    @coroutine
    def post(self, model, **kwargs):
        raise HTTPError(406, reason='My own error')


@provides(MediaType.TextHtml)
@provides(MediaType.ApplicationJson, default=True)
@consumes(MediaType.ApplicationJson, SimpleModel)
class MyWorkingModelHandler(RequestHandler):

    @coroutine
    def post(self, model, **kwargs):
        response_model = SimpleModel({'doc_id': 'id', 'doc_bool': True})
        raise Return(response_model)


@provides(MediaType.TextHtml)
@provides(MediaType.ApplicationJson, default=True)
@consumes(MediaType.ApplicationJson, SimpleModel)
class MyExceptionHandler(RequestHandler):
    @coroutine
    def get(self, *args, **kwargs):
        raise Exception('My exception')


class MyService(Service):
    def run(self):
        env = self.environment
        env.add_handler('/test', MySimpleHandler, {})
        env.add_handler('/test-model', MyModelHandler, {})
        env.add_handler('/test-error', MyErrorHandler, {})
        env.add_handler('/test-exception', MyExceptionHandler, {})
        env.add_handler('/test-model-no-error', MyWorkingModelHandler, {})


class ApplicationIntegrationTest(AsyncHTTPTestCase):
    @pytest.fixture(autouse=True)
    def empty_commandline(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [])

    def get_app(self):
        service = MyService()
        service.initialize_logging()
        return service.get_app()

    def eval_json(self, response, code):
        body = json.loads(response.body.decode('utf8'))
        self.assertIn('message', body)
        self.assertIn('error', body)
        self.assertEqual(code, response.code)

    def eval_html(self, response, code):
        self.assertEqual(code, response.code)
        self.assertTrue(response.body.decode('utf8').startswith('<html>'))
        self.assertEqual(code, response.code)

    def test_that_returning_non_model_is_an_error(self):
        response = self.fetch('/test', headers={'Accept': 'application/json'})
        self.eval_json(response, 500)

        response = self.fetch('/test', headers={'Accept': 'text/html'})
        self.eval_html(response, 500)

    def test_that_requesting_unknown_content_type_is_an_error(self):
        response = self.fetch('/test', method='POST',
                              body='...',
                              headers={'Content-Type': 'unknown'})
        self.eval_json(response, 400)

        response = self.fetch('/test', method='POST',
                              body='...',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 400)

    def test_that_rogue_field_in_model_is_an_error(self):
        response = self.fetch('/test-model',
                              method='POST',
                              body='{"unknown":"true"}',
                              headers={'Content-Type': 'application/json'})
        self.eval_json(response, 400)

        response = self.fetch('/test-model',
                              method='POST',
                              body='{"unknown":"true"}',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 400)

    def test_that_wrong_type_in_model_is_an_error(self):
        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"unknown"}',
                              headers={'Content-Type': 'application/json'})
        self.eval_json(response, 400)

        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"unknown"}',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 400)

    def test_that_wrong_accept_type_is_an_error(self):
        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"unknown"}',
                              headers={'Accept': 'application/unexpected',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 406)

        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"unknown"}',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/unexpected'}
                              )
        self.eval_html(response, 400)

    def test_that_empty_accept_type_works(self):
        response = self.fetch('/test-model-no-error', method='POST',
                              body='{"doc_id":"id", "doc_bool":"true"}',
                              headers={'Accept': '',
                                       'Content-Type': 'application/json'})
        self.assertEqual(200, response.code)

        response = self.fetch('/test-model-no-error', method='POST',
                              body='{"doc_id":"id", "doc_bool":"true"}',
                              headers={'Accept': '*/*',
                                       'Content-Type': 'application/json'})
        self.assertEqual(200, response.code)

    def test_that_invalid_return_model_is_an_error(self):
        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"True"}',
                              headers={'Content-Type': 'application/json'})
        self.eval_json(response, 500)

        response = self.fetch('/test-model', method='POST',
                              body='{"doc_id":"id", "doc_bool":"True"}',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 500)

    def test_that_individual_error_is_an_error(self):
        # supercell.mediatypes.Error
        response = self.fetch('/test-error')
        self.eval_json(response, 406)

        # TODO: supercell.mediatypes.Error produces NO html, fixing this would be a break!
        # response = self.fetch('/test-error',
        #                       headers={'Accept': 'text/html'})
        # self.eval_html(response, 406)

        # tornado.web.HTTPError
        response = self.fetch('/test-error', method='POST',
                              body='{"doc_id":"id", "doc_bool":"True"}',
                              headers={'Content-Type': 'application/json'})
        self.eval_json(response, 406)

        response = self.fetch('/test-error', method='POST',
                              body='{"doc_id":"id", "doc_bool":"True"}',
                              headers={'Accept': 'text/html',
                                       'Content-Type': 'application/json'})
        self.eval_html(response, 406)

    def test_that_exception_is_an_error(self):
        response = self.fetch('/test-exception')
        self.eval_json(response, 500)

        response = self.fetch('/test-exception',
                              headers={'Accept': 'text/html'})
        self.eval_html(response, 500)
