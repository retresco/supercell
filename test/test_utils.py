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
import pytest

from supercell.utils import escape_contents


PLAIN_STRING = 'string'
TAG_STRING = '<b>string</b>'
ESCAPED_TAG_STRING = '&lt;b&gt;string&lt;/b&gt;'


@pytest.mark.parametrize('source,expected', [
    [PLAIN_STRING, PLAIN_STRING],
    [TAG_STRING, ESCAPED_TAG_STRING],
    [[PLAIN_STRING], [PLAIN_STRING]],
    [[TAG_STRING], [ESCAPED_TAG_STRING]],
    [
        {PLAIN_STRING: TAG_STRING},
        {PLAIN_STRING: ESCAPED_TAG_STRING}
    ],
    [
        {TAG_STRING: PLAIN_STRING},
        {ESCAPED_TAG_STRING: PLAIN_STRING}
    ],
    [{PLAIN_STRING}, {PLAIN_STRING}],
    [{TAG_STRING}, {ESCAPED_TAG_STRING}],
    [
        (TAG_STRING, PLAIN_STRING),
        (ESCAPED_TAG_STRING, PLAIN_STRING)
    ],
    [
        {
            TAG_STRING: [(TAG_STRING,)]
        },
        {
            ESCAPED_TAG_STRING: [(ESCAPED_TAG_STRING,)]
        },
    ],
])
def test_escaping(source, expected):
    """
    Tests that escaped input matches expected output
    """
    assert escape_contents(source) == expected
