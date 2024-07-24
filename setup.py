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

from setuptools import setup

from supercell.version import __version__


tests_require = [
    'mock',
    'pytest',
    'pytest-cov'
]


extras_require = {}
extras_require['test'] = tests_require
extras_require['futures'] = ''


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='supercell',
    version=__version__,

    author='Daniel Truemper',
    author_email='truemped@gmail.com',
    url='http://supercell.readthedocs.org/',
    license="http://www.apache.org/licenses/LICENSE-2.0",

    description='Supercell is a framework for creating RESTful APIs that ' +
                'loosely follow the idea of domain driven design.',
    long_description=readme(),
    packages=['supercell'],

    install_requires=[
        'tornado >=4.2.1, <6.3',
        'schematics >= 1.1.1'
    ],

    tests_require=tests_require,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
    ]
)
