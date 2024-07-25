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

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import socket


class SupercellLoggingHandler(TimedRotatingFileHandler):
    """Logging handler for :mod:`supercell` applications.
    """

    def __init__(self, logfile):
        """Initialize the :class:`TimedRotatingFileHandler`."""
        logfile = logfile % {'pid': os.getpid()}
        TimedRotatingFileHandler.__init__(self, logfile, when='d',
                                          interval=1, backupCount=10)


class HostnameFormatter(logging.Formatter):
    """
    Formatter that adds a hostname field to the LogRecord
    """
    def format(self, record):
        record.hostname = socket.gethostname()
        record = super().format(record)
        return record
