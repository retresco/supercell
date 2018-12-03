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

from datetime import datetime
import json
import logging
import time
import inspect

from schematics.models import Model
from schematics.types.compound import ListType
from schematics.exceptions import BaseError
from tornado import gen, iostream
from tornado.concurrent import is_future
from tornado.escape import to_unicode
from tornado.util import bytes_type, unicode_type
from tornado.web import (RequestHandler as rq, HTTPError,
                         _has_stream_request_body)

from supercell._compat import error_messages, text_type
from supercell.cache import compute_cache_header
from supercell.mediatypes import Error, MediaType, ReturnInformationT
from supercell.consumer import ConsumerBase, NoConsumerFound
from supercell.provider import ProviderBase, NoProviderFound


__all__ = ['RequestHandler']


_DEFAULT_CONTENT_TYPE = 'DEFAULT'


def _decode_utf8_and_latin1(value):
    """Convert an string argument to a unicode string.

    Instead of decoding it as utf-8 we assume it is encoded as latin1.
    """
    try:
        return to_unicode(value)
    except UnicodeDecodeError:
        if isinstance(value, (unicode_type, type(None))):
            return value
        assert isinstance(value, bytes_type), \
            'Expected bytes, unicode or None; got %s' % type(value)
        return value.decode('latin1')


class RequestHandler(rq):
    """**supercell** request handler.

    The only difference to the :class:`tornado.web.RequestHandler` is an
    adopted :func:`RequestHandler._execute()` method that will handle
    the consuming and providing of request inputs and results.
    """

    @property
    def environment(self):
        """Convenience method for accessing the environment."""
        return self.application.environment

    @property
    def config(self):
        """Convenience method for accessing the configuration."""
        return self.application.config

    @property
    def logger(self):
        """Use this property to write to the log files.

        In a request handler you would simply log messages like this::

            def get(self):
                self.logger.info('A test')
        """
        if not hasattr(self, '_logger'):
            name = '%s:%s' % (self.__class__.__name__, self.request_id)
            self._logger = logging.getLogger(name)
        return self._logger

    def decode_argument(self, value, name=None):
        """Overwrite the default :func:`RequestHandler.decode_argument()`
        method in order to allow *latin1* encoded URLs.
        """
        return _decode_utf8_and_latin1(value)

    @property
    def request_id(self):
        """Return a unique id per request. Collisions are allowed but should
        should not occur within a 10 minutes time window.

        The current implementation is based on a timestamp in milliseconds
        substracted by a large number to make the id smaller.
        """
        if not hasattr(self, '_request_id'):
            self._request_id = int(time.time() * 1000) - 1374400000000
        return self._request_id

    def _request_summary(self):
        """Returns a summery of method, uri, caller ip and request id.
        If request is forwarded by a proxy and X-Forwarded-For header is set,
        the ip from this header is use as caller ip.
        The message is mainly used for log messages."""
        x_forward = self.request.headers.get('X-Forwarded-For', None)
        return '{method} {uri} (ip:{r_ip}, r_id:{r_id})'.format(
            method=self.request.method,
            uri=self.request.uri,
            r_ip=x_forward or self.request.remote_ip,
            r_id=str(self.request_id),
        )

    def get_template(self, model):
        """Method to determine which template to use for rendering the html.
        """
        raise NotImplementedError

    def _check_consumer(self):
        """For a PATCH, POST, or PUT request check if we can find a matching
        consumer for the incoming data."""
        verb = self.request.method.lower()
        headers = self.request.headers
        kwargs = self.path_kwargs

        if verb in ['patch', 'post', 'put'] and 'Content-Type' in headers:
            # try to find a matching consumer
            try:
                (model, consumer_class) = ConsumerBase.map_consumer(
                    headers['Content-Type'], self)
                consumer = consumer_class()
                kwargs['model'] = consumer.consume(self, model)
            except NoConsumerFound:
                # TODO return available consumer types?!
                raise HTTPError(400, reason='Content-Type not supported.')
            except BaseError as e:
                raise HTTPError(400, reason=json.dumps(error_messages(e)))
            except Exception as e:
                raise HTTPError(400, reason=text_type(e))

    def _add_cache_headers(self):
        """Maybe add cache headers on GET and HEAD requests."""
        verb = self.request.method.lower()
        if verb in ['get', 'head']:
            # check if there is caching information stored with the handler
            cache_config = self.environment.get_cache_info(self.__class__)
            if cache_config:
                self.set_header('Cache-Control',
                                compute_cache_header(cache_config))

            expires = self.environment.get_expires_info(self.__class__)
            if expires:
                self.set_header('Expires', datetime.now() + expires)

    @gen.coroutine
    def prepare(self):
        """Check for a consumer and optionally add the cache headers.

        note:: when overriding the `prepare()` method, don't forget to call
               the super method.
        """
        self._check_consumer()
        self._add_cache_headers()

    @gen.coroutine
    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms.

        This is basically a copy of tornado's `_execute()` method. The only
        difference is the expected result. Tornado expects the result to be
        `None`, where we want this to be a :py:class:Model."""
        verb = self.request.method.lower()
        headers = self.request.headers
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise HTTPError(405)
            self.path_args = [self.decode_argument(arg) for arg in args]
            self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()

            result = self.prepare()
            if is_future(result):
                result = yield result
            if result is not None:
                # TODO: provide all results in this case or only errors?
                if type(result) is ReturnInformationT:
                    self._provide_result(verb, headers, result)
                else:
                    raise TypeError("Expected None, got %r" % result)
            if self._prepared_future is not None:
                # Tell the Application we've finished with prepare()
                # and are ready for the body to arrive.
                self._prepared_future.set_result(None)
            if self._finished:
                return

            if _has_stream_request_body(self.__class__):
                # In streaming mode request.body is a Future that signals
                # the body has been completely received.  The Future has no
                # result; the data has been passed to self.data_received
                # instead.
                try:
                    yield self.request.body
                except iostream.StreamClosedError:
                    return

            method = getattr(self, self.request.method.lower())
            result = method(*self.path_args, **self.path_kwargs)
            if is_future(result) or inspect.iscoroutinefunction(method):
                result = yield result
            if result is not None:
                self._provide_result(verb, headers, result)
            if self._auto_finish and not self._finished:
                self.finish()
        except Exception as e:
            self._handle_request_exception(e)
            if (self._prepared_future is not None and
                    not self._prepared_future.done()):
                # In case we failed before setting _prepared_future, do it
                # now (to unblock the HTTP server).  Note that this is not
                # in a finally block to avoid GC issues prior to Python 3.4.
                self._prepared_future.set_result(None)

    def _provide_result(self, verb, headers, result):
        """Find the correct provider for the result and call it with the final
        result."""

        if isinstance(result, ReturnInformationT):
            self.set_header('Content-Type', MediaType.ApplicationJson)
            self.set_status(result.code)
            if result.message and 'additional' in result.message:
                self.logger.info(result.message['additional'])
            if result.code != 204:
                self.write(json.dumps(result.message))

        elif not isinstance(result, Model):
            # raise an error when something else than a model has been returned
            self.logger.error('Returning a non-model is not supported')
            raise HTTPError(500)

        else:
            try:
                provider_class, provider_config = ProviderBase.map_provider(
                    headers.get('Accept', ''), self, allow_default=True)
            except NoProviderFound:
                raise HTTPError(406)

            provider = provider_class()
            if isinstance(result, Model):
                provider.provide(result, self, **provider_config)

        if not self._finished:
            self.finish()

    def write_error(self, status_code, **kwargs):
        try:
            provider_class, _ = ProviderBase.map_provider(
                self.request.headers.get('Accept', ''), self,
                allow_default=True)
            provider_class().error(status_code, self._reason, self)
        except NoProviderFound:
            super(RequestHandler, self).write_error(status_code, **kwargs)

    def load_model_from_arguments(self, model_cls, validate=True, **kwargs):
        """
        Convenience method for instantiating a model from the request's url
        query arguments. Supports ListType model fields for multi parameters.
        Kwargs can specify defaults for fields not provided in the request.

        :param model_cls: A model class (instance of schematics.models.Model).
        :param validate : Allows to switch off validation (default is True).
        :param kwargs   : Optional arguments that are used as default if there
                          is no adequate parameter in request.

        :return: A model instance.
        """
        assert issubclass(model_cls, Model)

        raw_data = dict(kwargs)
        fields = model_cls._fields  # noqa

        arguments = {
            key: self.get_arguments(key)
            for key in self.request.query_arguments
        }

        raw_data.update({
            key: (
                values
                if isinstance(fields.get(key, None), ListType)
                else values[0]
            )
            for key, values in arguments.items() if values
        })
        model = model_cls(raw_data)
        if validate:
            model.validate()
        return model

    def _handle_request_exception(self, e):
        """
        convert supercell errors to tornado errors so they can be used
        in handlers defined with the async/await syntax
        """
        if isinstance(e, Error):
            e = HTTPError(status_code=e.value.code, msg=e.value.message)
        super(RequestHandler, self)._handle_request_exception(e)
