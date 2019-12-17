# Set default logging handler to avoid "No handler found" warnings.
import logging

from pymogilefs import backend, client, exceptions

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
