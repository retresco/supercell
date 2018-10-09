# -*- coding: utf-8 -*-
# Copyright (c) 2018 Retresco GmbH <support@retresco.de>

from logging import makeLogRecord
import mock
from unittest import TestCase

from supercell.logging import HostnameFormatter


class TestHostnameFormatter(TestCase):

    def test_hostname_in_format_string(self):
        with mock.patch('socket.gethostname', return_value='horst'):
            formatter = HostnameFormatter('%(hostname)s - %(message)s')
            record = makeLogRecord({'msg': 'test123'})
            log = formatter.format(record)
            self.assertEqual(log, 'horst - test123')
