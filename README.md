pymogilefs
==========

Python client for MogileFS.


## Feature highlight

This implementation has some unique production-ready features, and have been used with large scale data-intensive 
applications (hundreds of nodes, several PBs, billions of files.) 

These includes:
* tracker load balancing
* test on borrow
* fault tolerance
* connection keep alive
* the [zone](https://github.com/mogilefs/perl-MogileFS-Client/blob/master/lib/MogileFS/Client.pm#L537) option a.k.a.  alternative IP   

## Install
To install pymogilefs, simply:

    $ git clone git@github.com:hrchu/pymogilefs.git
    $ cd pymogilefs
    $ pip install .

## Example

Client usage:

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

Admin usage:

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

Ref more examples in `example/example.py`.

## Multithreading / Multiprocessing
Note that it is recommended to create a resource instance for each thread / process in a multithreaded or multiprocess 
application rather than sharing a single instance among the threads / processes.


## Acknowledges
There are a few Python client projects for MogileFS around, however, these projects seem to be outdated and abandoned. 
This work is based on [one](https://github.com/bwind/pymogilefs) of them. Many thanks!

## Contributing
Forks and pull requests are highly appreciated.

