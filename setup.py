# vim: set fileencoding=utf-8 :
#
# Copyright (c) 2012 Daniel Truemper <truemped at googlemail.com>
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
from imp import load_source
import os
from setuptools import setup
import sys


init = load_source('init', os.path.join('supercell', '__init__.py'))
PY2 = sys.version_info[0] == 2


tests_require = [
    'mock',
    'pytest',
    'pytest-cov'
]

if sys.version_info < (2, 7):
    tests_require.append('unittest2')


extras_require = {}
extras_require['test'] = tests_require
extras_require['futures'] = ''
if PY2:
    extras_require['futures'] = 'futures == 2.2.0'


setup(
    name='supercell',
    version=init.__version__,

    author='Daniel Truemper',
    author_email='truemped@gmail.com',
    url='http://supercell.readthedocs.org/',
    license="http://www.apache.org/licenses/LICENSE-2.0",

    description='Supercell is a framework for creating RESTful APIs that ' +
                'loosely follow the idea of domain driven design.',
    packages=['supercell'],

    install_requires=[
        'tornado',
        'schematics',
        'scales'
    ],

    tests_require=tests_require,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
