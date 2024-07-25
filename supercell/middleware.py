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

from abc import ABCMeta, abstractmethod
from functools import wraps

from schematics.models import Model
from tornado.gen import coroutine, Return

from supercell._compat import with_metaclass
from supercell.mediatypes import ReturnInformationT


class Middleware(with_metaclass(ABCMeta, object)):
    """Base class for middleware implementations.

    Each request handler is assigned a list of `Middleware` implementations.
    Before a handler is called, each middleware is executed using the
    `Middleware.before` method. When the underlying handler is finished, the
    `Middleware.after` method may manipulate the result.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the decorator and register the `after()` callback."""
        pass

    def __call__(self, fn):
        """Call the `before()` method and then the decorated method. If this
        returns a `Future`, add the `after()` method as a `done` callback.
        Otherwise execute it immediately.
        """

        @coroutine
        @wraps(fn)
        def before(other, *args, **kwargs):
            before_result = yield self.before(other, args, kwargs)

            if isinstance(before_result, (ReturnInformationT, Model)):
                raise Return(before_result)

            result = yield fn(other, *args, **kwargs)

            after_result = yield self.after(other, args, kwargs, result)

            if isinstance(after_result, (ReturnInformationT, Model)):
                raise Return(after_result)

            raise Return(result)

        return before

    @abstractmethod
    def before(self, handler, args, kwargs):
        """Method executed before the underlying request handler is called."""

    @abstractmethod
    def after(self, handler, args, kwargs, result):
        """Method executed after the unterlying request handler ist called."""
