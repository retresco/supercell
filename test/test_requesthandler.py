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

import pytest

import json
import os.path as op

import schematics
from schematics.models import Model
from schematics.types import StringType
from schematics.types import IntType
from schematics.types.compound import ListType
from schematics.types.compound import ModelType

from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

import supercell.api as s
from supercell.api import (RequestHandler, provides, consumes)
from supercell.environment import Environment


class SimpleMessage(Model):
    doc_id = StringType()
    message = StringType()
    number = IntType()

    class Options:
        serialize_when_none = False


@provides(s.MediaType.ApplicationJson)
class MyHandler(RequestHandler):

    @s.async
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


@provides(s.MediaType.ApplicationJson, default=True)
class MyHandlerWithDefault(RequestHandler):

    @s.async
    def get(self, *args, **kwargs):
        raise s.Return(SimpleMessage({"doc_id": 'test123',
                                      "message": 'A test'}))


@consumes(s.MediaType.ApplicationJson, SimpleMessage)
@provides(s.MediaType.ApplicationJson, default=True)
class MyEchoHandler(RequestHandler):

    @s.async
    def get(self, *args, **kwargs):
        q = self.get_argument('q')
        # query solr:
        raise s.Return(SimpleMessage({"doc_id": 'test456',
                                      "message": 'q: %s' % q}))

    @s.async
    def post(self, *args, **kwargs):
        # do something with model
        raise s.OkCreated({'docid': 123})

    @s.async
    def patch(self, *args, **kwargs):
        # do something with model
        raise s.Ok()

    @s.async
    def delete(self, *args, **kwargs):
        raise s.NoContent()


class TestSimpleRequestHandler(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_handler('/test', MyHandler)
        env.add_handler('/test_default', MyHandlerWithDefault)
        env.add_handler('/test_echo', MyEchoHandler)
        return env.get_application()

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_simple_handler(self):
        response = self.fetch('/test', headers={'Accept':
                                                s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        self.assertEqual('{"doc_id": "test123", "message": "A test"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

    def test_handler_without_accept(self):
        response = self.fetch('/test')
        self.assertEqual(response.code, 406)

    def test_default_handler(self):
        response = self.fetch('/test_default')
        self.assertEqual(response.code, 200)
        self.assertEqual('{"doc_id": "test123", "message": "A test"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

    def test_handler_with_missing_provider(self):
        response = self.fetch('/test', headers={'Accept':
                                                'application/vnd.supercell+xml'
                                                })
        self.assertEqual(response.code, 406)

    def test_post_handler(self):
        response = self.fetch('/test_echo', method='POST',
                              headers={'Content-Type':
                                       s.MediaType.ApplicationJson},
                              body='{"message": "Simple message", "number": 1}'
                              )
        self.assertEqual(response.code, 201)
        self.assertEqual('{"docid": 123, "ok": true}', json.dumps(json.loads(
            response.body.decode('utf8')), sort_keys=True))

    def test_post_handler_with_wrong_value_type(self):
        response = self.fetch('/test_echo', method='POST',
                              headers={'Content-Type':
                                       s.MediaType.ApplicationJson},
                              body='{"number": "one"}')
        self.assertEqual(response.code, 400)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {
            'error': True,
            'message': {'number': ["Value 'one' is not int."]}
        })

    def test_patch_handler(self):
        response = self.fetch('/test_echo', method='PATCH',
                              headers={'Content-Type':
                                       s.MediaType.ApplicationJson},
                              body='{"number": 100}'
                              )
        self.assertEqual(response.code, 200)
        self.assertEqual('{"ok": true}', json.dumps(json.loads(
            response.body.decode('utf8')), sort_keys=True))

    def test_patch_handler_with_wrong_value_type(self):
        response = self.fetch('/test_echo', method='PATCH',
                              headers={'Content-Type':
                                       s.MediaType.ApplicationJson},
                              body='{"number": "one"}'
                              )
        self.assertEqual(response.code, 400)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {
            'error': True,
            'message': {'number': ["Value 'one' is not int."]}
        })

    def test_delete(self):
        response = self.fetch('/test_echo', method='DELETE')
        self.assertEqual(response.code, 204)


@provides(s.MediaType.ApplicationJson, default=True)
class EncodingTestingHandler(s.RequestHandler):

    @s.async
    def get(self, *args, **kwargs):
        json_args = json.dumps(args)
        json_kwargs = json.dumps(kwargs)
        r = SimpleMessage({"doc_id": 'test123',
                           "message": 'args=%s; kwargs=%s' % (json_args,
                                                              json_kwargs)})
        raise s.Return(r)


class TestUrlEncoding(AsyncHTTPTestCase):

    def get_app(self):
        env = Environment()
        env.add_handler('/testencoding/(.*)', EncodingTestingHandler)
        return env.get_application()

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_latinone_handler(self):
        response = self.fetch('/testencoding/alfredo-p%e9rez-rubalcaba')
        self.assertEqual(200, response.code)
        self.assertEqual('{"doc_id": "test123", "message": "' +
                         'args=[\\"alfredo-p\\\\u00e9rez-rubalcaba\\"]; ' +
                         'kwargs={}"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

    def test_utfeight_handler(self):
        response = self.fetch('/testencoding/alfredo-p%C3%A9rez-rubalcaba')
        self.assertEqual(200, response.code)
        self.assertEqual('{"doc_id": "test123", "message": "' +
                         'args=[\\"alfredo-p\\\\u00e9rez-rubalcaba\\"]; ' +
                         'kwargs={}"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))


class TestSimpleHtmlHandler(AsyncHTTPTestCase):

    def get_app(self):

        @provides(s.MediaType.TextHtml, default=True)
        class SimpleHtmlHandler(s.RequestHandler):

            def get_template(self, model):
                return 'test.html'

            @s.async
            def get(self, *args, **kwargs):
                r = SimpleMessage({'doc_id': 'test123',
                                   'message': 'bliblablup'})
                raise s.Return(r)

        env = Environment()
        env.add_handler('/test_html/(.*)', SimpleHtmlHandler)
        d = op.dirname(__file__)
        env.tornado_settings['template_path'] = op.join(d,
                                                        'html_test_template')
        return env.get_application()

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_simple_html(self):
        response = self.fetch('/test_html/')
        self.assertEqual(200, response.code)
        exp_html = ("<html>\n<head><title>Test</title></head>\n" +
                    "<body>\ndoc_id: test123\nmessage: bliblablup\n" +
                    "</body>\n</html>\n")
        self.assertEqual(exp_html, response.body.decode('utf8'))


class TestSimpleHtmlHandlerWithMissingTemplate(AsyncHTTPTestCase):

    def get_app(self):

        @provides(s.MediaType.TextHtml, default=True)
        class SimpleHtmlHandler(s.RequestHandler):

            @s.async
            def get(self, *args, **kwargs):
                r = SimpleMessage({'doc_id': 'test123',
                                   'message': 'args=%s; kwargs=%s' % (args,
                                                                      kwargs)})
                raise s.Return(r)

        env = Environment()
        env.add_handler('/test_html/(.*)', SimpleHtmlHandler)
        d = op.dirname(__file__)
        env.tornado_settings['template_path'] = op.join(d,
                                                        'html_test_template')
        return env.get_application()

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_simple_html(self):
        response = self.fetch('/test_html/')
        self.assertEqual(500, response.code)


class StricterMessage(Model):
    doc_id = StringType(required=True)
    message = StringType(required=True)
    number = IntType()

    class Options:
        serialize_when_none = False


class StricterMessageCollection(Model):
    messages = ListType(ModelType(StricterMessage))


class TestHandlerProvidingPartialModels(AsyncHTTPTestCase):

    def get_app(self):

        @provides(s.MediaType.ApplicationJson)
        class MyHandlerWithoutPartial(RequestHandler):

            @s.async
            def get(self, *args, **kwargs):
                raise s.Return(StricterMessage({"doc_id": 'test123'}))

        @provides(s.MediaType.ApplicationJson, partial=True)
        class MyHandlerWithPartial(RequestHandler):

            @s.async
            def get(self, *args, **kwargs):
                raise s.Return(StricterMessage({"doc_id": 'test123'}))

        @provides(s.MediaType.ApplicationJson, partial=True)
        class MyHandlerWithPartialComplex(RequestHandler):

            @s.async
            def get(self, *args, **kwargs):
                raise s.Return(StricterMessageCollection(
                    {"messages": [{"doc_id": 'test123'}]}))

        env = Environment()
        env.add_handler('/test_no_partial', MyHandlerWithoutPartial)
        env.add_handler('/test_partial', MyHandlerWithPartial)
        env.add_handler('/test_partial_complex', MyHandlerWithPartialComplex)
        return env.get_application()

    def get_new_ioloop(self):
        return IOLoop.instance()

    def test_provide_partial_model_with_partial_false(self):
        response = self.fetch(
            '/test_no_partial',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 500)
        self.assertEqual(
            '{"error": true, "message": {"result_model": ' +
            '{"message": ["This field is required."]}}}',
            json.dumps(json.loads(response.body.decode('utf8')),
                       sort_keys=True))

    def test_provide_partial_model_with_partial_true(self):
        response = self.fetch(
            '/test_partial',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        self.assertEqual('{"doc_id": "test123"}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))

    @pytest.mark.skipif(
        schematics.__version__ < "2.0.1",
        reason="Partial validation of complex models is broken in schematics" +
               " version < 2.0.1.")
    def test_provide_partial_model_with_complex_partial_true(self):
        response = self.fetch(
            '/test_partial_complex',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        self.assertEqual('{"messages": [{"doc_id": "test123"}]}',
                         json.dumps(json.loads(response.body.decode('utf8')),
                                    sort_keys=True))


class SimpleModel(Model):
    name = StringType()
    numbers = ListType(IntType())

    class Options:
        serialize_when_none = False


class TestLoadModelFromArguments(AsyncHTTPTestCase):

    def get_app(self):

        @provides(s.MediaType.ApplicationJson, default=True)
        class MyHandler(RequestHandler):

            @s.async
            def get(self, *args, **kwargs):
                model = self.load_model_from_arguments(
                    SimpleModel, name="default")
                raise s.Return(model)

        env = Environment()
        env.add_handler('/test', MyHandler)
        return env.get_application()

    def test_load_model_default_is_used(self):
        response = self.fetch(
            '/test',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {"name": "default"})

    def test_load_model_default_is_overwritten(self):
        response = self.fetch(
            '/test?name=Peter',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {"name": "Peter"})

    def test_load_model_list_type_single_entries(self):
        response = self.fetch(
            '/test?name=Peter&numbers=1',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {"name": "Peter", "numbers": [1]})

    def test_load_model_list_type_multiple_entries(self):
        response = self.fetch(
            '/test?name=Peter&numbers=1&numbers=2&numbers=3',
            headers={'Accept': s.MediaType.ApplicationJson})
        self.assertEqual(response.code, 200)
        body = json.loads(response.body.decode('utf8'))
        self.assertEqual(body, {"name": "Peter", "numbers": [1, 2, 3]})
