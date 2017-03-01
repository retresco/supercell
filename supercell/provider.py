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

import json
from collections import defaultdict
from schematics.exceptions import ModelValidationError
from tornado.web import HTTPError
from tornado import escape

from supercell._compat import with_metaclass
from supercell.mediatypes import ContentType, MediaType
from supercell.acceptparsing import parse_accept_header

__all__ = ['NoProviderFound', 'ProviderBase', 'JsonProvider']


class NoProviderFound(Exception):
    """Raised if no matching provider for the client's `Accept` header was
    found."""
    pass


class ProviderMeta(type):
    """Meta class for all content type providers.

    This will simply register a provider with the respective content type
    information and make them available in a list of content types and their
    mappers.
    """

    KNOWN_CONTENT_TYPES = defaultdict(list)

    def __new__(cls, name, bases, dct):
        provider_class = type.__new__(cls, name, bases, dct)

        if name != 'ProviderBase' and hasattr(provider_class, 'CONTENT_TYPE'):
            ct = provider_class.CONTENT_TYPE
            ProviderMeta.KNOWN_CONTENT_TYPES[ct.content_type].append(
                (ct, provider_class))

        return provider_class


class ProviderBase(with_metaclass(ProviderMeta, object)):
    """Base class for content type providers.

    Creating a new provider is just as simple as creating new consumers::

        class MyProvider(s.ProviderBase):

            CONTENT_TYPE = s.ContentType('application/xml')

            def provide(self, model, handler):
                self.set_header('Content-Type', 'application/xml')
                handler.write(model.to_xml())
    """

    CONTENT_TYPE = None
    """The target content type for the provider.

    :type: `supercell.api.ContentType`
    """

    @staticmethod
    def map_provider(accept_header, handler, allow_default=False):
        """Map a given content type to the correct provider implementation.

        If no provider matches, raise a `NoProviderFound` exception.

        :param accept_header: HTTP Accept header value
        :type accept_header: str
        :param handler: supercell request handler
        :param allow_default: allow usage of default provider if no accept header is set, default is False
        :type allow_default: bool
        :raises: :exc:`NoProviderFound`
        """
        if not hasattr(handler, '_PROD_CONTENT_TYPES'):
            raise NoProviderFound()

        accept = parse_accept_header(accept_header)

        if len(accept) > 0:
            for (ctype, params, q) in accept:
                if ctype not in handler._PROD_CONTENT_TYPES:
                    continue

                c = ContentType(ctype, vendor=params.get('vendor', None),
                                version=params.get('version', None))
                if c not in handler._PROD_CONTENT_TYPES[ctype]:
                    continue

                known_types = [t for t in
                               ProviderMeta.KNOWN_CONTENT_TYPES[ctype]
                               if t[0] == c]

                if len(known_types) == 1:
                    return known_types[0][1]

        if allow_default and 'default' in handler._PROD_CONTENT_TYPES:
            content_type = handler._PROD_CONTENT_TYPES['default']
            ctype = content_type.content_type
            default_type = [t for t in
                            ProviderMeta.KNOWN_CONTENT_TYPES[ctype]
                            if t[0] == content_type]

            if len(default_type) == 1:
                return default_type[0][1]

        raise NoProviderFound()

    def provide(self, model, handler):
        """This method should return the correct representation as a simple
        string (i.e. byte buffer) that will be used as return value.

        :param model: the model to convert to a certain content type
        :type model: supercell.schematics.Model
        """
        raise NotImplementedError

    def error(self, status_code, message, handler):
        """This method should return the correct representation of errors
        that will be used as return value.

        :param status_code: the HTTP status code to return
        :type status_code: int
        :param message: the error message to return
        :type message: str
        :param handler: the handler to write the return
        :type handler: supercell.requesthandler.RequestHandler
        """
        raise NotImplementedError


class JsonProvider(ProviderBase):
    """Default `application/json` provider."""

    CONTENT_TYPE = ContentType(MediaType.ApplicationJson)

    def provide(self, model, handler):
        """Simply return the json via `json.dumps`.

        .. seealso:: :py:mod:`supercell.api.provider.ProviderBase.provide`
        """
        try:
            model.validate()
            handler.write(model.to_primitive())
        except ModelValidationError as e:
            # TODO: How to let know, that result model is concerned?
            e.messages = {"result_model": e.messages}
            raise HTTPError(500, reason=json.dumps(e.messages))

    def error(self, status_code, message, handler):
        """Simply return the json.

        .. seealso:: :py:mod:`supercell.api.provider.ProviderBase.error`
        """
        try:
            message = json.loads(message)
        except ValueError:
            pass

        res = {"message": message,
               "error": True}
        handler.set_header('Content-Type', MediaType.ApplicationJson)
        handler.finish(escape.json_encode(res))


class TornadoTemplateProvider(ProviderBase):
    """Default provider for `text/html`."""

    CONTENT_TYPE = ContentType(MediaType.TextHtml)

    def provide(self, model, handler):
        """Render a template with the given model into HTML.

        By default we will use the tornado built in template language."""
        try:
            model.validate()
            handler.render(handler.get_template(model), **model.to_primitive())
        except ModelValidationError as e:
            # TODO: How to let know, that result model is concerned?
            e.messages = {"result_model": e.messages}
            raise HTTPError(500, reason=json.dumps(e.messages))

    def error(self, status_code, message, handler):
        """ Return errors in html

        .. seealso:: :py:mod:`supercell.api.provider.ProviderBase.error`
        """
        handler.finish("<html><title>%(code)d: %(message)s</title>"
                       "<body>%(code)d: %(message)s</body></html>" % {
                           "code": status_code,
                           "message": message,
                       })
