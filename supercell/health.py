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
"""Health checks provide a way for the hoster to check if the application is
still running and working as expected.

The most basic health check is enabled by default on the */_system/check*
route. This is a very simple check if the process is running and provides no
details to your application checks.

To demonstrate the idea we will describe a simple health check perfoming a
request to a HTTP resource and return the appropriate result::

    @s.provides(s.MediaType.ApplicationJson, default=True)
    class SimpleHttpResourceCheck(s.RequestHandler):

        @s.async
        def get(self):
            result = self.environment.http_resource.ping()
            if result.code == 200:
                raise s.HealthCheckOk()
            if result.code == 599:
                raise s.HealthCheckError()

To enable this health check simply add this to the environment in your services
run method::

    class MyService(s.Service):

        def run(self):
            self.environment.add_health_check('http_resource',
                                              SimpleHttpResourceCheck)

When the service is then started you can access the check as
*/_system/check/http_resource*::

    $ curl 'http://127.0.0.1/_system/check/http_resource'
    {"code": "OK", "ok": true}

The HTTP response code will be **200** when everything is ok. Any error,
**WARNING** or **ERROR** will return the HTTP code **500**. A warning will
return the response::

    $ curl 'http://127.0.0.1/_system/check/http_resource_with_warning'
    {"code": "WARNING", "error": true}

and an error a similar one::

    $ curl 'http://127.0.0.1/_system/check/http_resource_with_warning'
    {"code": "ERROR", "error": true}
"""
from __future__ import (absolute_import, division, print_function,
                        with_statement)

from tornado.gen import coroutine

from supercell.decorators import provides
from supercell.mediatypes import Ok, Error, MediaType
from supercell.requesthandler import RequestHandler


class HealthCheckOk(Ok):
    """Exception for health checks return values indicating a **OK**
    health check."""

    def __init__(self, additional=None):
        """Initialize the health checks response."""
        additional = additional or {}
        additional['code'] = 'OK'
        super(HealthCheckOk, self).__init__(code=200, additional=additional)


class HealthCheckWarning(Error):
    """Exception for health checks return values indicating a
    **WARNING** health check.

    The **WARNING** state indicates a problem that is not critical to the
    application. This could involve things like long response and similar
    problems."""

    def __init__(self, additional=None):
        """Initialize the health checks response."""
        additional = additional or {}
        additional['code'] = 'WARNING'
        super(HealthCheckWarning, self).__init__(code=500,
                                                 additional=additional)


class HealthCheckError(Error):
    """Exception for health checks return values indicating a
    **ERROR** health check.

    The **ERROR** state indicates a major problem like a failed connection to a
    database."""

    def __init__(self, additional=None):
        """Initialize the health checks response."""
        additional = additional or {}
        additional['code'] = 'ERROR'
        super(HealthCheckError, self).__init__(code=500,
                                               additional=additional)


@provides(MediaType.ApplicationJson, default=True)
class SystemHealthCheck(RequestHandler):
    """The default system health check.

    This check is returning this JSON::

        {"message": "API running", "code": "OK", "ok": true}

    and its primiary use is to check if the process is still running and
    working as expected. If this request takes too long to respond, and all
    other systems are working correctly, you probably need to create more
    instances of the service since the current number of processes cannot
    deal with the number of requests coming from the outside.
    """

    @coroutine
    def get(self):
        """Run the default **/_system** healthcheck and return it's result."""
        raise HealthCheckOk(additional={'message': 'API running'})
