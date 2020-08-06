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
from unittest import TestCase

from supercell.api import consumes, RequestHandler
from supercell.mediatypes import ContentType, MediaType
from supercell.consumer import (ConsumerBase, JsonConsumer,
                                         NoConsumerFound)


class MoreDetailedJsonConsumer(JsonConsumer):

    CONTENT_TYPE = ContentType(MediaType.ApplicationJson, vendor='supercell')


class JsonConsumerWithVendorAndVersion(JsonConsumer):

    CONTENT_TYPE = ContentType(MediaType.ApplicationJson, vendor='supercell',
                               version=1.0)


class TestBasicConsumer(TestCase):

    def test_default_json_consumer(self):

        @consumes(MediaType.ApplicationJson, object)
        class MyHandler(RequestHandler):
            pass

        (_, consumer) = ConsumerBase.map_consumer(MediaType.ApplicationJson,
                                                  handler=MyHandler)

        self.assertIs(consumer, JsonConsumer)

        with self.assertRaises(NoConsumerFound):
            ConsumerBase.map_consumer('application/vnd.supercell-v1.1+json',
                                      handler=MyHandler)

    def test_default_json_consumer_with_encoding_in_ctype(self):

        @consumes(MediaType.ApplicationJson, object)
        class MyHandler(RequestHandler):
            pass

        (_, consumer) = ConsumerBase.map_consumer(
            'application/json; encoding=UTF-8', handler=MyHandler)

        self.assertIs(consumer, JsonConsumer)

        with self.assertRaises(NoConsumerFound):
            ConsumerBase.map_consumer('application/vnd.supercell-v1.1+json',
                                      handler=MyHandler)

    def test_specific_json_consumer(self):

        @consumes(MediaType.ApplicationJson, object, vendor='supercell')
        class MyHandler(RequestHandler):
            pass

        (_, consumer) = ConsumerBase.map_consumer(
            'application/vnd.supercell+json', handler=MyHandler)
        self.assertIs(consumer, MoreDetailedJsonConsumer)

        with self.assertRaises(NoConsumerFound):
            ConsumerBase.map_consumer(MediaType.ApplicationJson,
                                      handler=MyHandler)

    def test_json_consumer_with_version(self):

        @consumes(MediaType.ApplicationJson, object, vendor='supercell',
                  version=1.0)
        class MyHandler(RequestHandler):
            pass

        (_, consumer) = ConsumerBase.map_consumer(
            'application/vnd.supercell-v1.0+json', handler=MyHandler)
        self.assertIs(consumer, JsonConsumerWithVendorAndVersion)

        with self.assertRaises(NoConsumerFound):
            ConsumerBase.map_consumer(MediaType.ApplicationJson,
                                      handler=MyHandler)
