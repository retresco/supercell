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
from collections import namedtuple
from types import FloatType


ContentTypeT = namedtuple('ContentType', ['content_type', 'vendor',
                                         'version', 'model'])

def ContentType(content_type, vendor=None, version=None, model=None):
    if version:
        assert isinstance(version, FloatType), 'Version must be a float'
    return ContentTypeT(content_type, vendor, version, model)
