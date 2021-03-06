import unittest

from pymogilefs.backend import GetHostsConfig
from pymogilefs.request import Request


class RequestTest(unittest.TestCase):
    def test_request_returns_bytes(self):
        request = Request(GetHostsConfig)
        self.assertIsInstance(bytes(request), bytes)

    def test_request_returns_newline_terminated_command(self):
        request = Request(GetHostsConfig)
        self.assertEqual(bytes(request), b'get_hosts \r\n')

    def test_request_with_args(self):
        request = Request(GetHostsConfig, test='foo')
        self.assertIn(b'test=foo', bytes(request))
