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
from schematics.models import Model
from schematics.types import StringType, IntType

from tornado.options import define

import supercell.api as s


define('default_name', 'World', help='Default name')
define('template', 'main.html', help='Tornado template file')


class Saying(Model):

    id = IntType()
    content = StringType()


@s.provides(s.MediaType.ApplicationJson, default=True)
class HelloWorld(s.RequestHandler):

    @property
    def counter(self):
        if not hasattr(self.__class__, '_counter'):
            self.__class__._counter = 0
        return self.__class__._counter or 0

    @counter.setter
    def counter(self, value):
        self.__class__._counter = value

    @s.coroutine
    def get(self):
        self.counter += 1
        name = self.get_argument('name', self.config.default_name)
        content = self.render_string(self.config.template, name=name)
        raise s.Return(Saying({'id': self.counter, 'content': content}))


class MyService(s.Service):

    def bootstrap(self):
        self.environment.config_file_paths.append('./etc')
        self.environment.config_file_paths.append('/etc/hello-world/')

    def run(self):
        self.environment.add_handler('/hello-world', HelloWorld)


def main():
    MyService().main()


if __name__ == '__main__':
    main()
