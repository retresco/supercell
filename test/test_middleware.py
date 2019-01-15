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

import json

from tornado.testing import AsyncHTTPTestCase

from schematics.models import Model
from schematics.types import StringType
from schematics.types import IntType

import supercell.api as s
from supercell.middleware import Middleware


class SimpleMessage(Model):
    doc_id = StringType()
    message = StringType()
    number = IntType()

    class Options:
        serialize_when_none = False


class ReturnOtherResult(Middleware):

    @s.coroutine
    def before(self, handler, args, kwargs):
        pass

    @s.coroutine
    def after(self, handler, args, kwargs, result):
        raise s.Return(SimpleMessage({"doc_id": "no way",
                                      "message": "forget about it!"}))


class AddDummyHeader(Middleware):

    @s.coroutine
    def before(self, handler, args, kwargs):
        yield self.add_another_header(handler)

    @s.coroutine
    def add_another_header(self, handler):
        handler.add_header('X-Dummy2', 'nice')
        raise s.Return(None)

    @s.coroutine
    def after(self, handler, args, kwargs, result):
        yield self.add_header(handler)

    @s.coroutine
    def add_header(self, handler):
        handler.add_header('X-Dummy', 'kewl')


class RewriteQueryParam(Middleware):

    @s.coroutine
    def before(self, handler, args, kwargs):
        arg = handler.get_argument('id', None)
        if arg:
            new_arg = arg.replace('test', 'TEST')
            handler.request.arguments['id'] = [new_arg]

    @s.coroutine
    def after(self, handler, args, kwargs, result):
        yield self.wait_a_little()

    @s.coroutine
    def wait_a_little(self):
        return


@s.provides(s.MediaType.ApplicationJson, default=True)
class MyHandler(s.RequestHandler):

    @AddDummyHeader()
    @RewriteQueryParam()
    @s.coroutine
    def get(self, *args, **kwargs):
        doc_id = self.get_argument('id', 'test123')
        model = yield self.get_message(doc_id)
        raise s.Return(model)

    @s.coroutine
    def get_message(self, doc_id):
        raise s.Return(SimpleMessage({"doc_id": doc_id,
                                      "message": 'A test'}))


@s.provides(s.MediaType.ApplicationJson, default=True)
class MyHandlerReturningOtherStuff(s.RequestHandler):

    @RewriteQueryParam()
    @ReturnOtherResult()
    @s.coroutine
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": "yo",
                                      "message": 'A test'}))


class TestDummyHeaderMiddleware(AsyncHTTPTestCase):

    def get_app(self):
        env = s.Environment()
        env.add_handler('/test', MyHandler)
        env.add_handler('/otherresult', MyHandlerReturningOtherStuff)
        return env.get_application()

    def test_that_header_exists(self):
        response = self.fetch('/test')

        assert response.code == 200, 'Something went wrong'
        assert 'X-Dummy' in response.headers, 'Header missing'
        assert response.headers.get('X-Dummy') == 'kewl', 'wrong header value?'
        assert '{"doc_id": "test123", "message": "A test"}' == json.dumps(
            json.loads(response.body.decode('utf8')), sort_keys=True)

    def test_manipulating_query_params(self):
        response = self.fetch('/test?id=test432')

        assert response.code == 200, 'Something went wrong'
        assert 'X-Dummy' in response.headers, 'Header missing'
        assert response.headers.get('X-Dummy') == 'kewl', 'wrong header value?'
        assert '{"doc_id": "TEST432", "message": "A test"}' == json.dumps(
            json.loads(response.body.decode('utf8')), sort_keys=True)

    def test_returning_other_data_in_after(self):
        response = self.fetch('/otherresult')

        assert response.code == 200, 'Something went wrong'
        assert '{"doc_id": "no way", "message": "forget about it!"}' == \
            json.dumps(json.loads(response.body.decode('utf8')),
                       sort_keys=True)
