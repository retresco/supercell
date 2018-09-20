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

from collections import defaultdict

import sys
if sys.version_info > (2, 7):
    from unittest import TestCase
else:
    from unittest2 import TestCase

from pytest import raises

from supercell.api import (RequestHandler, provides, consumes, MediaType)


class TestConsumesDecorator(TestCase):
    '''Test the consumes decorator.'''

    def test_on_non_class(self):

        with raises(AssertionError):
            @consumes(MediaType.ApplicationJson, object)
            def get():
                pass

    def test_simple_consumes_decorator_with_post(self):

        @consumes(MediaType.ApplicationJson, object)
        class MyHandler(RequestHandler):

            _CONS_CONTENT_TYPES = defaultdict(list)

            def post(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_CONS_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._CONS_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._CONS_CONTENT_TYPES)
        content_type = MyHandler._CONS_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertIsNone(content_type.vendor)
        self.assertIsNone(content_type.version)
        self.assertEqual(MyHandler._CONS_MODEL[content_type], (object, True))

    def test_consumes_decorator_with_vendor_info(self):

        @consumes(MediaType.ApplicationJson, object, vendor='ficture.light',
                  version=1.0)
        class MyHandler(RequestHandler):

            def post(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_CONS_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._CONS_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._CONS_CONTENT_TYPES)
        content_type = MyHandler._CONS_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertEqual(content_type.vendor, 'ficture.light')
        self.assertEqual(content_type.version, 1.0)
        self.assertEqual(MyHandler._CONS_MODEL[content_type], (object, True))

    def test_consumes_decorator_with_model(self):

        @consumes(MediaType.ApplicationJson, object, validate=False)
        class MyHandler(RequestHandler):

            def post(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_CONS_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._CONS_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._CONS_CONTENT_TYPES)
        content_type = MyHandler._CONS_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertIsNone(content_type.vendor)
        self.assertIsNone(content_type.version)
        self.assertEqual(MyHandler._CONS_MODEL[content_type], (object, False))


class TestProvidesDecorator(TestCase):
    '''Test the consumes decorator.'''

    def test_on_non_class(self):

        with raises(AssertionError):
            @provides(MediaType.ApplicationJson)
            def get():
                pass

    def test_simple_provides_decorator_with_post(self):

        @provides(MediaType.ApplicationJson)
        class MyHandler(RequestHandler):
            _PROD_CONTENT_TYPES = defaultdict(list)

            pass

        self.assertTrue(hasattr(MyHandler, '_PROD_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._PROD_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._PROD_CONTENT_TYPES)
        content_type = MyHandler._PROD_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertIsNone(content_type.vendor)
        self.assertIsNone(content_type.version)

    def test_provides_decorator_with_vendor_info(self):

        @provides(MediaType.ApplicationJson, 'ficture.light', version=1.0)
        class MyHandler(RequestHandler):

            def update_stuff(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_PROD_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._PROD_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._PROD_CONTENT_TYPES)
        content_type = MyHandler._PROD_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertEqual(content_type.vendor, 'ficture.light')
        self.assertEqual(content_type.version, 1.0)

    def test_provides_decorator_with_model(self):

        @provides(MediaType.ApplicationJson)
        class MyHandler(RequestHandler):

            def update_stuff(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_PROD_CONTENT_TYPES'))
        self.assertEqual(len(MyHandler._PROD_CONTENT_TYPES), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._PROD_CONTENT_TYPES)
        content_type = MyHandler._PROD_CONTENT_TYPES[
            MediaType.ApplicationJson][0]
        self.assertEqual(content_type.content_type,
                         MediaType.ApplicationJson)
        self.assertIsNone(content_type.vendor)
        self.assertIsNone(content_type.version)

    def test_provides_decorator_with_partial(self):

        @provides(MediaType.ApplicationJson, partial=True)
        class MyHandler(RequestHandler):

            def update_stuff(self):
                pass

        self.assertTrue(hasattr(MyHandler, '_PROD_CONFIGURATION'))
        self.assertEqual(len(MyHandler._PROD_CONFIGURATION), 1)
        self.assertTrue(MediaType.ApplicationJson in
                        MyHandler._PROD_CONFIGURATION)
        configuration = MyHandler._PROD_CONFIGURATION[
            MediaType.ApplicationJson]
        self.assertIs(configuration["partial"], True)
