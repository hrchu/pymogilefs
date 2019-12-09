pymogilefs
==========

Python client for MogileFS, based on https://github.com/bwind/pymogilefs.

There are a few Python client projects for MogileFS around, however, these projects seem to be outdated and
abandoned. This implementation adds some production necessary features (tracker load balancing, test on borrow, fault tolerance, and so on), and have been used with large scale data-intensive applications (hundreds of nodes, several PBs, billions of files.)

To install pymogilefs, simply:

    $ pip install pymogilefs

Usage:

    >>> from pymogilefs.client import Client
    >>> client = Client(trackers=['0.0.0.0:7001'], domain='testdomain')
    >>> response = client.list_keys(prefix='test', limit=5)
    >>> print(response.data)
    {'key_count': 5,
     'keys': {1: 'testkey',
              2: 'test_file2_0.115351657953_1480606271.65',
              3: 'test_file2_0.380149553659_1480606080.71',
              4: 'test_file_0.0129341319339_1480606080.74',
              5: 'test_file_0.0397767495074_1480606080.8'},
     'next_after': 'testkey'}
    >>> buf = client.get_file('testkey')
    >>> len(buf.read())
    4

Backend usage:

    >>> from pymogilefs.backend import Backend
    >>> backend = Backend(trackers=['0.0.0.0:7001'])
    >>> devices = backend.get_devices()
    >>> print(devices.data['devices']['9'])
    {'devid': '16',
     'hostid': '5',
     'mb_asof': '',
     'mb_free': '45181',
     'mb_total': '59640',
     'mb_used': '14459',
     'observed_state': '',
     'reject_bad_md5': '',
     'status': 'dead',
     'utilization': '',
     'weight': '100'}

Forks and pull requests are highly appreciated.
