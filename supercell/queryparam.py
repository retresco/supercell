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
"""Simple decorator for dealing with typed query parameters."""
from __future__ import (absolute_import, division, print_function,
                        with_statement)

from schematics.exceptions import ConversionError, ValidationError

import supercell.api as s
from supercell._compat import error_messages


class QueryParams(s.Middleware):
    """Simple middleware for ensuring types in query parameters.

    A simple example::

        @QueryParams((
            ('limit', IntType()),
            ('q', StringType())
            )
        )
        @s.async
        def get(self, *args, **kwargs):
            limit = kwargs.get('limit', 0)
            q = kwargs.get('q', None)
            ...

    If a param is required, simply set the `required` property for the
    schematics type definition::

        @QueryParams((
            ('limit', IntType(required=True)),
            ('q', StringType())
            )
        )
        ...

    If the parameter is missing, a HTTP 400 error is raised.

    By default the dictionary containing the typed query parameters is added
    to the `kwargs` of the method with the key *query*. In order to change
    that, simply change the key in the definition::

        @QueryParams((
            ...
            ),
            kwargs_name='myquery'
        )
        ...
    """

    def __init__(self, params, kwargs_name='query'):
        super(QueryParams, self).__init__()
        self.params = params
        self.kwargs_name = kwargs_name

    @s.coroutine
    def before(self, handler, args, kwargs):
        kwargs[self.kwargs_name] = q = {}
        for (name, typedef) in self.params:
            if handler.get_argument(name, None):
                try:
                    parsed = typedef(handler.get_argument(name))
                    q[name] = parsed
                except (ConversionError, ValidationError) as e:
                    validation_errors = {name: error_messages(e)}
                    raise s.Error(additional=validation_errors)
            elif typedef.required and not handler.get_argument(name, None):
                raise s.Error(additional={'msg':
                                          'Missing required argument "%s"' %
                                          name})

    @s.coroutine
    def after(self, handler, args, kwargs, result):
        pass
