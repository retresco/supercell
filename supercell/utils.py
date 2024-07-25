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

from html import escape


__all__ = ['escape_contents']


def escape_contents(o):
    """
    Encodes chars <, > and & as HTML entities.
    """
    _e = escape_contents
    if isinstance(o, str):
        return escape(o, quote=False)
    elif isinstance(o, dict):
        o = {_e(k): _e(o[k]) for k in o}
    elif isinstance(o, list):
        o = [_e(v) for v in o]
    elif isinstance(o, tuple):
        o = tuple(_e(v) for v in o)
    elif isinstance(o, set):
        o = {_e(v) for v in o}
    return o
