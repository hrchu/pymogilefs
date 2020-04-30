import socket

from pymogilefs.exceptions import MogilefsError
from pymogilefs.request import Request
from pymogilefs.response import Response

BUFSIZE = 4096
TIMEOUT = 15


class Connection:
    def __init__(self, host, port):
        self._host = host
        self._port = int(port)
        self._sock = None

    def __str__(self):
        return ':'.join([self._host, str(self._port)])

    def is_connected(self):
        return self._sock is not None

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((self._host, self._port))
        self._sock = sock

    def noop(self):
        self._sock.send('noop\r\n'.encode())
        response_text = self._recv_all()
        if 'OK' not in response_text:
            raise MogilefsError('NOT OK', 'noop failed')

    def _recv_all(self):
        response_text = b''
        while True:
            received = self._sock.recv(BUFSIZE)
            response_text += received
            if response_text[-2:] == b'\r\n':
                break
        return response_text.decode()

    def close(self):
        try:
            self._sock.close()
        finally:
            self._sock = None

    def do_request(self, request):
        assert isinstance(request, Request)
        self._sock.send(bytes(request))
        response_text = self._recv_all()
        return Response(response_text, request.config)
