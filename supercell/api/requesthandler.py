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
from __future__ import absolute_import, division, print_function, with_statement
from functools import partial
import json

from tornado import gen
from tornado.web import RequestHandler as rq, HTTPError

from supercell.api import Ok, Error, Return
from supercell.api.metatypes import ReturnInformationT
from supercell.api.consumer import ConsumerBase, NoConsumerFound
from supercell.api.provider import ProviderBase, NoProviderFound


__all__ = ['RequestHandler']


_DEFAULT_CONTENT_TYPE = 'DEFAULT'


class RequestHandler(rq):
    '''
    Supercell request handler.
    '''

    def __init__(self, *args, **kwargs):
        '''Initialize the request and map the instance methods to the HTTP
        verbs.'''
        super(RequestHandler, self).__init__(*args, **kwargs)

    def _execute_method(self):
        '''
        Execute the request.

        The method to be executed is determined by the request method.
        '''
        if not self._finished:
            verb = self.request.method.lower()
            headers = self.request.headers
            method = getattr(self, verb)
            kwargs = self.path_kwargs

            if verb in ['post', 'put'] and 'Content-Type' in headers:
                # try to find a matching consumer
                try:
                    (model, consumer_class) = ConsumerBase.map_consumer(
                            headers['Content-Type'], self)
                    consumer = consumer_class()
                    kwargs['model'] = consumer.consume(self, model)
                except NoConsumerFound:
                    # TODO return available consumer types?!
                    raise HTTPError(406)

            future_model = method(*self.path_args, **kwargs)

            callback = partial(self._provide_result, verb, headers)
            future_model.add_done_callback(callback)

    def _provide_result(self, verb, headers, future_model):
        '''Find the correct provider for the result and call it with the final
        result.'''
        result = future_model.result()

        if isinstance(result, ReturnInformationT):
            self.set_header('Content-Type', 'application/json')
            self.set_status(result.code)
            self.write(json.dumps(result.message))

        else:
            try:
                provider_class = ProviderBase.map_provider(
                        headers.get('Accept', ''), self, allow_default=True)
            except NoProviderFound:
                raise HTTPError(406)

            provider = provider_class()
            if future_model.result():
                provider.provide(future_model.result(), self)
            else:
                provider.provide(Ok, self)
        self.finish()
