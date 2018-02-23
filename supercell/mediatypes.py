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
from collections import namedtuple

from tornado import gen


ContentTypeT = namedtuple('ContentType', ['content_type', 'vendor',
                                          'version'])


def ContentType(content_type, vendor=None, version=None):
    if version:
        assert isinstance(version, float), 'Version must be a float'
    return ContentTypeT(content_type, vendor, version)


class MediaType(object):
    """Collection of content types."""

    ApplicationJson = 'application/json'
    """Content type for `application/json`"""

    ApplicationJsonPatch = 'application/json-patch+json'
    """Content type for `application/json-patch+json`"""

    TextHtml = 'text/html'
    """Content type for `text/html`"""


ReturnInformationT = namedtuple('ReturnInformation', ['code', 'message'])


def ReturnInformation(code, message=None):
    return ReturnInformationT(code, message=message)


class Return(gen.Return):
    pass


class Ok(Return):

    def __init__(self, code=200, additional=None):
        v = {'ok': True}
        if additional:
            assert isinstance(additional, dict), 'Additional messages must ' +\
                                                 'be of type dict'
            v.update(additional)

        super(Ok, self).__init__(ReturnInformation(code, message=v))


class OkCreated(Ok):

    def __init__(self, additional=None):
        super(OkCreated, self).__init__(201, additional=additional)


class NoContent(Return):

    def __init__(self):
        super(NoContent, self).__init__(ReturnInformation(204))


class Error(Return):

    def __init__(self, code=400, additional=None):
        v = {'error': True}
        if additional:
            assert isinstance(additional, dict), 'Additional messages must ' +\
                                                 'be of type dict'
            v.update(additional)

        super(Error, self).__init__(ReturnInformation(code, message=v))
