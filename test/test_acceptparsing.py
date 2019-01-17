# vim: set fileencoding=utf-8 :
#
# Taken from: https://gist.github.com/samuraisam/2714195
#
from unittest import TestCase

from supercell.acceptparsing import parse_accept_header


class TestParseAcceptHeader(TestCase):
    def test_parse_accept_header_browser(self):
        accept = ("text/html,application/xhtml+xml,application/xml;" +
                  "q=0.9,*/*;q=0.8,application/json")
        should = [('text/html', {}, 1.0),
                  ('application/xhtml+xml', {}, 1.0),
                  ('application/json', {}, 1.0),
                  ('application/xml', {}, 0.9),
                  ('*/*', {}, 0.8)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_smart_client(self):
        accept = "application/vnd.ficture.lightt-v1.1+json"
        should = [('application/json', {'version': 1.1,
                                        'vendor': 'ficture.lightt'}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_smart_client_without_version(self):
        accept = "application/vnd.ficture.lightt+json"
        should = [('application/json', {'vendor': 'ficture.lightt'}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_dumbish_client(self):
        accept = "application/vnd.ficture.lightt-v1.0"
        should = [('application/vnd.ficture.lightt-v1.0', {}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_also_dumb_client(self):
        accept = "application/vnd.ficture.lightt"
        should = [('application/vnd.ficture.lightt', {}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_dumb_client(self):
        accept = "application/json"
        should = [('application/json', {}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_parse_accept_header_really_dumb_client(self):
        accept = ""
        should = [('*/*', {}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)

    def test_iesix_bad_accept_header(self):
        accept = 'text/*,image/*;application/*;*/*;'
        should = [('*/*', {}, 1.0)]
        self.assertEquals(parse_accept_header(accept), should)
