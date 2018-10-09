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
"""A :class:`Service` is the main element of a `supercell` application. It will
instanciate the :class:`supercell.api.Environment` and parse the configuration
files as well as the command line. In the final step the
:class:`tornado.web.Application` is created and bound to a socket.
"""
from __future__ import (absolute_import, division, print_function,
                        with_statement)

import logging
from logging import StreamHandler
import os
import signal
import socket
import sys
import time

import tornado.options
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define

from supercell.environment import Environment
from supercell.logging import HostnameFormatter, SupercellLoggingHandler


define('logfile', default='root-%(pid)s.log',
       help='Filename to store the logs. If the name contains "%%(pid)s" ' +
       'it will be replaced with the pid. If the filename equals to "-" ' +
       'the logs are being written to stdout')


define('loglevel', default='INFO', help='Log level')

define('logformat', default='%(asctime)s [%(levelname)s] %(hostname)s ' +
       '%(name)s:  %(message)s', help='format string for logging formatter')

define('suppress_health_check_log', default=False,
       help='Suppress the access logging for the system health check.')

define('port', default=8080, help='Port to listen on')


define('address', default='127.0.0.1', help='Address to bind on')


define('socketfd', default=None, help='Filedescriptor used from circus')


define('max_grace_seconds', default=3,
       help='Wait up to this amount of seconds to finish requests before ' +
       'shutdown')


define('debug', default=False, help='If set, Tornado is started in debug mode')


define('show_config_file_order', default=False,
       help='Show the order of config files to be parsed')


define('show_config_name', default=False,
       help='Show the local config file name')


define('show_config', default=False,
       help='Show the effective configuration')


class Service(object):
    """Main service implementation managing the
    :class:`tornado.web.Application` and taking care of configuration."""

    def main(self, with_signals=True):
        """Main method starting a **supercell** process.

        This will first instantiate the :class:`tornado.web.Application` and
        then bind it to the socket. There are two possibilities to bind to a
        socket: either by binding to a certain port and address as defined by
        the configuration (the *port* and *address* configuration settings) or
        by the *socketfd* command line parameter.

        The latter is mainly used in combination with Circus
        (http://circus.readthedocs.org/). There you would bind the socket from
        circus and start the worker processes by binding to the file
        descriptor.
        """
        app = self.get_app()

        self.server = HTTPServer(app)

        if self.config.socketfd:
            sock = socket.fromfd(int(self.config.socketfd), socket.AF_INET,
                                 socket.SOCK_STREAM)
            self.server.add_socket(sock)
        else:
            self.server.bind(self.config.port, address=self.config.address)
            self.server.start(1)

        if with_signals:
            def sig_handler(sig, frame):
                IOLoop.current().add_callback(self.shutdown)    # noqa
            signal.signal(signal.SIGTERM, sig_handler)
            signal.signal(signal.SIGINT, sig_handler)

        self.slog.info('Starting supercell')
        IOLoop.current().start()

    def shutdown(self):
        """Gaceful shutdown of the server.

        In this method we stop the `tornado.httpserver` in order to stop
        accepting new connections. During a period of `max_grace_seconds`
        current requests are allowed to finish. After this period the `IOLoop`
        is stopped.
        """
        io_loop = IOLoop.current()
        self.slog.info('Stopping HTTP server')
        self.server.stop()

        dl = time.time() + self.config.max_grace_seconds

        def stop_loop():
            now = time.time()
            if now < dl and self._has_callbacks(io_loop):
                io_loop.add_timeout(now + 1, stop_loop)
            else:
                io_loop.stop()
                self.slog.info('Shutdown')
        stop_loop()

    def get_app(self):
        """Create the :class:`tornado.web.Appliaction` instance and return it.

        In this method the :func:`Service.bootstrap()` is called, then
        :func:`Service.run()` will initialize the app."""

        # initialize the environment
        self.environment

        # bootstrap the service
        self.bootstrap()

        # perform all the configuration parsing
        self.config

        # hook some mgmt commands
        if self.config.show_config:
            from pprint import pprint
            pprint(self.config.as_dict())
            raise SystemExit(1)

        if self.config.show_config_name:
            print(self.environment.config_name)
            raise SystemExit(1)

        if self.config.show_config_file_order:
            filename = self.environment.config_name
            for path in self.environment.config_file_paths:
                print(os.path.join(path, 'config.cfg'))
                print(os.path.join(path, filename))
            raise SystemExit(1)

        # initialize logging
        self.initialize_logging()

        # add handlers, health checks, managed objects to the environment
        self.run()

        # do not allow any changes on the environment anymore.
        self.environment._finalize()

        self.environment.tornado_settings['debug'] = self.config.debug

        return self.environment.get_application(self.config)

    @property
    def slog(self):
        """Initialize the logging and return the logger."""
        if not hasattr(self, '_slog'):
            self._slog = logging.getLogger('supercell')
        return self._slog

    @property
    def environment(self):
        """The default environment instance."""
        if not hasattr(self, '_environment'):
            self._environment = Environment()
        return self._environment

    @property
    def config(self):
        """Assemble the configration files and command line arguments in order
        to finalize the service's configuration. All configuration values
        can be overwritten by the command line and/or environment variables.

        precedence:
            command line arguments > environment variables > config file
        """
        if not hasattr(self, '_config'):
            # parse config files and command line arguments
            self.parse_config_files()
            from tornado.options import options
            self.parse_environment_variables(options)
            self.parse_command_line()
            self._config = options
        return self._config

    def parse_config_files(self):
        """Parse the config files and return the `config` object, i.e. the
        `tornado.options.options` instance. For each entry in the
        `Environment.config_file_paths()` it will check for a general
        *config.py* and then for a file named as defined by
        `Environment.config_name`.

        So if the config file paths are set to `['/etc/myservice',
        './etc/']` the following files are parsed::

            /etc/myservice/config.cfg
            /etc/myservice/user_hostname.cfg
            ./etc/config.cfg
            ./etc/user_hostname.cfg

        .. note::
            By default we disable the :py:mod:`tornado.log` module, you can
            enable this though using by setting the `logging` config to some
            valid log level string.
        """
        tornado.options.options._options['logging'].set('none')
        filename = self.environment.config_name
        for path in self.environment.config_file_paths:
            cfg = os.path.join(path, 'config.cfg')
            if os.path.exists(cfg):
                tornado.options.parse_config_file(cfg)

            cfg = os.path.join(path, filename)
            if os.path.exists(cfg):
                tornado.options.parse_config_file(cfg)

    def parse_command_line(self):
        """Parse the command line arguments to set different configuration
        values."""
        tornado.options.parse_command_line()

    def parse_environment_variables(self, options, final=True):
        """
        Parse environment variables to set different configuration values.
        """
        for name in options:
            env = os.getenv(name.replace('-', '_').upper())
            if env is not None:
                options._options[options._normalize_name(name)].parse(env)

        if final:
            options.run_parse_callbacks()

    def initialize_logging(self):
        """Initialize the python logging system.

        It is difficult to check whether the logging system is already
        initialized, so we are currently only checking if a
        :class:`SupercellLoggingHandler` has already been added to the `root`
        logger. This should only be necessary when running unittests though."""
        root = logging.getLogger()

        if self.config.logfile == '-':
            clazz = StreamHandler
            logfile = sys.stdout
        else:
            clazz = SupercellLoggingHandler
            logfile = self.config.logfile

        hdlrs = [h for h in root.handlers
                 if isinstance(h, clazz)]
        if len(hdlrs) == 0:
            root.setLevel(getattr(logging, self.config.loglevel))
            hdlr = clazz(logfile)
            formatter = HostnameFormatter(self.config.logformat)

            hdlr.setFormatter(formatter)
            root.addHandler(hdlr)

    def bootstrap(self):
        """Implement this method in order to manipulate the configuration
        paths, e.g.."""
        pass

    def run(self):
        """Implement this method in order to add handlers and managed objects
        to the environment, before the app is started."""
        pass

    def _has_callbacks(self, io_loop):
        """Check if the io_loop has pending callbacks.

        The check works with the default io_loop as well as the asyncio loop.
        You may have to override it for other implemations.
        """
        if hasattr(tornado.platform, "asyncio") and isinstance(
            io_loop, tornado.platform.asyncio.AsyncIOMainLoop
        ):
            return io_loop.asyncio_loop._scheduled
        else:
            return (io_loop._callbacks or io_loop._timeouts)
