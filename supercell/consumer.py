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

from collections import defaultdict
import json

from supercell._compat import with_metaclass
from supercell.mediatypes import ContentType, MediaType
from supercell.acceptparsing import parse_accept_header


__all__ = ['NoConsumerFound', 'ConsumerBase', 'JsonConsumer']


class NoConsumerFound(Exception):
    """Raised if no matching consumer for the client's `Content-Type` header
    was found."""
    pass


class ConsumerMeta(type):
    """Meta class for all consumers.

    This will simply register a consumer with the respective content type
    information and make them available in a list of content types and their
    consumer.
    """

    KNOWN_CONTENT_TYPES = defaultdict(list)

    def __new__(cls, name, bases, dct):
        consumer_class = type.__new__(cls, name, bases, dct)

        if name != 'ConsumerBase' and hasattr(consumer_class, 'CONTENT_TYPE'):
            ct = consumer_class.CONTENT_TYPE
            ConsumerMeta.KNOWN_CONTENT_TYPES[ct.content_type].append(
                (ct, consumer_class))

        return consumer_class


class ConsumerBase(with_metaclass(ConsumerMeta, object)):
    """Base class for content type consumers.

    In order to create a new consumer, you must create a new class that
    inherits from :py:class:`ConsumerBase` and sets the
    :data:`ConsumerBase.CONTENT_TYPE` variable::

        class MyConsumer(s.ConsumerBase):

            CONTENT_TYPE = s.ContentType('application/xml')

            def consume(self, handler, model):
                return model(lxml.from_string(handler.request.body))

    .. seealso:: :py:mod:`supercell.api.consumer.JsonConsumer.consume`
    """

    CONTENT_TYPE = None
    """The target content type for the consumer.

    :type: `supercell.api.ContentType`
    """

    @staticmethod
    def map_consumer(content_type, handler):
        """Map a given content type to the correct provider implementation.

        If no provider matches, raise a `NoProviderFound` exception.

        :param accept_header: HTTP Accept header value
        :type accept_header: str
        :param handler: supercell request handler

        :raises: :exc:`NoConsumerFound`
        """
        accept = parse_accept_header(content_type)
        if len(accept) == 0:
            raise NoConsumerFound()

        (ctype, params, q) = accept[0]

        if ctype not in handler._CONS_CONTENT_TYPES:
            raise NoConsumerFound()

        c = ContentType(ctype, vendor=params.get('vendor', None),
                        version=params.get('version', None))
        if c not in handler._CONS_CONTENT_TYPES[ctype]:
            raise NoConsumerFound()

        known_types = [t for t in ConsumerMeta.KNOWN_CONTENT_TYPES[ctype]
                       if t[0] == c]

        if len(known_types) == 1:
            return (handler._CONS_MODEL[c], known_types[0][1])

        raise NoConsumerFound()

    def consume(self, handler, model):
        """This method should return the correct representation as a parsed
        model.

        :param model: the model to convert to a certain content type
        :type model: :class:`schematics.models.Model`
        """
        raise NotImplementedError


class JsonConsumer(ConsumerBase):
    """Default **application/json** consumer."""

    CONTENT_TYPE = ContentType(MediaType.ApplicationJson)
    """The **application/json** :class:`ContentType`."""

    def consume(self, handler, model):
        """Parse the body json via :func:`json.loads` and initialize the
        `model`.

        .. seealso:: :py:mod:`supercell.api.provider.ProviderBase.provide`
        """
        # TODO error if no request body is set
        return model(json.loads(handler.request.body.decode('utf8')))


class JsonPatchConsumer(JsonConsumer):
    """Default **application/json-patch+json** consumer."""

    CONTENT_TYPE = ContentType(MediaType.ApplicationJsonPatch)
    """The **application/json-patch+json** :class:`ContentType`."""
