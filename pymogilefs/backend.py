import logging
import random
import re
import socket
import time
from typing import Dict

from pymogilefs.connection import Connection
from pymogilefs.exceptions import MogilefsError
from pymogilefs.request import Request

"""
Backend manages a pool of trackers and balances load between them.
"""

# TODO: Implement a real pool for thread-safe.


MAX_RETRIES = 5
FORGIVENESS_TIME = 5 * 60

log = logging.getLogger(__name__)


class Backend:
    def __init__(self, trackers):
        self._trackers = [[Connection(*tracker.split(':')), 0] for tracker in trackers]

    def _get_not_failed_lately_connection_idx(self) -> int:
        max_try = 1000
        for j in range(max_try):
            i = random.randrange(len(self._trackers))
            connection, last_failed_time = self._trackers[i]

            if time.time() - last_failed_time < FORGIVENESS_TIME:
                continue

            return i

        raise Exception('Seems all connections are failed lately.')

    def _get_connection(self) -> Connection:
        connection = None
        max_try = min(MAX_RETRIES, len(self._trackers))
        for j in range(max_try):
            i = self._get_not_failed_lately_connection_idx()
            tracker_info = self._trackers[i]
            candidate, last_failed_time = tracker_info
            log.debug("Try #%s/%s time using tracker: %s", j + 1, max_try, candidate)

            if not candidate.is_connected():
                try:
                    candidate._connect()
                except socket.error as exc:
                    log.warning("Caught socket.error while connecting the tracker: '%s'", candidate._host,
                                canexc_info=exc)
                    tracker_info[1] = time.time()
                    continue

            try:
                candidate.noop()
            except MogilefsError as exc:
                log.warning("Caught MogilefsError while nooping the tracker: '%s'", candidate._host, exc_info=exc)
                tracker_info[1] = time.time()
                try:
                    candidate.close()
                except Exception:
                    pass
                continue

            connection = candidate
            break

        if connection:
            return connection
        else:
            raise Exception('No tracker usable.')

    def do_request(self, config, **kwargs):
        return self._get_connection().do_request(Request(config, **kwargs))

    def get_hosts(self):
        return self.do_request(GetHostsConfig)

    def create_host(self, host, ip, port):
        return self.do_request(CreateHostConfig, host=host, ip=ip, port=port)

    def update_host(self, host, ip, port):
        return self.do_request(UpdateHostConfig, host=host, ip=ip, port=port)

    def delete_host(self, host):
        return self.do_request(DeleteHostConfig, host=host)

    def get_domains(self):
        return self.do_request(GetDomainsConfig)

    def create_domain(self, domain):
        return self.do_request(CreateDomainConfig, domain=domain)

    def delete_domain(self, domain):
        return self.do_request(DeleteDomainConfig, domain=domain)

    def get_classes(self):
        raise NotImplementedError

    def create_class(self, domain, _class, mindevcount):
        kwargs = {'domain': domain,
                  'class': _class,
                  'mindevcount': mindevcount}
        return self.do_request(CreateClassConfig, **kwargs)

    def update_class(self, domain, _class, mindevcount):
        kwargs = {'domain': domain,
                  'class': _class,
                  'mindevcount': mindevcount}
        return self.do_request(UpdateClassConfig, **kwargs)

    def delete_class(self, domain, _class):
        kwargs = {'domain': domain,
                  'class': _class}
        return self.do_request(DeleteClassConfig, **kwargs)

    def get_devices(self):
        return self.do_request(GetDevicesConfig)

    def create_device(self, hostname, devid, hostip, state):
        return self.do_request(CreateDeviceConfig,
                               hostname=hostname,
                               devid=devid,
                               hostip=hostip,
                               state=state)

    def set_state(self, host, device, state):
        return self.do_request(SetStateConfig,
                               host=host,
                               device=device,
                               state=state)

    def set_weight(self, host, device, weight):
        return self.do_request(SetWeightConfig,
                               host=host,
                               device=device,
                               weight=weight)


def parse_response_text(response_text) -> Dict:
    try:
        return dict([pair.split('=') for pair in response_text.split('&')])
    except ValueError:
        raise Exception('Cannot parse response: %s', response_text)


class RequestConfig:
    @classmethod
    def parse_response_text(cls, response_text):
        if not response_text or response_text == '':
            return {}
        return parse_response_text(response_text)


class GetHostsConfig(RequestConfig):
    COMMAND = 'get_hosts'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        if 'hosts' in pairs:
            del pairs['hosts']
        hosts = {}
        for key, value in pairs.items():
            idx, unprefixed_key = key[4:].split('_', 1)
            idx = int(idx)
            if idx not in hosts:
                hosts[idx] = {}
            hosts[idx][unprefixed_key] = value
        return {'hosts': hosts}


class CreateHostConfig(RequestConfig):
    COMMAND = 'create_host'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        return {key.split('host', 1)[1]: value for key, value in pairs.items()}


class UpdateHostConfig(RequestConfig):
    COMMAND = 'update_host'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        return {key.split('host', 1)[1]: value for key, value in pairs.items()}


class DeleteHostConfig(RequestConfig):
    COMMAND = 'delete_host'


class GetDomainsConfig(RequestConfig):
    COMMAND = 'get_domains'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        if 'domains' in pairs:
            del pairs['domains']
        domains = {}
        pattern = r'^domain([0-9]+)class([0-9]+)([a-z]+)$'
        for key, value in pairs.items():
            domain_id, class_id, unprefixed_key = re.match(pattern,
                                                           key).groups()
            domain_id = int(domain_id)
            class_id = int(class_id)
            if domain_id not in domains:
                domains[domain_id] = {'classes': {}}
            if class_id not in domains[domain_id]['classes']:
                domains[domain_id]['classes'][class_id] = {}
            domains[domain_id]['classes'][class_id][unprefixed_key] = value
        return {'domains': domains}


class CreateDomainConfig(RequestConfig):
    COMMAND = 'create_domain'


class DeleteDomainConfig(RequestConfig):
    COMMAND = 'delete_domain'


class CreateClassConfig(RequestConfig):
    COMMAND = 'create_class'


class UpdateClassConfig(RequestConfig):
    COMMAND = 'update_class'


class DeleteClassConfig(RequestConfig):
    COMMAND = 'delete_class'


class GetDevicesConfig(RequestConfig):
    COMMAND = 'get_devices'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        if 'devices' in pairs:
            del pairs['devices']
        devices = {}
        for key, value in pairs.items():
            idx, unprefixed_key = key[3:].split('_', 1)
            if idx not in devices:
                devices[idx] = {}
            devices[idx][unprefixed_key] = value
        return {'devices': devices}


class CreateDeviceConfig(RequestConfig):
    COMMAND = 'create_device'


class SetStateConfig(RequestConfig):
    COMMAND = 'set_state'


class SetWeightConfig(RequestConfig):
    COMMAND = 'set_weight'


class CreateOpenConfig(RequestConfig):
    COMMAND = 'create_open'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        data = {
            'fid': pairs['fid'],
            'dev_count': int(pairs['dev_count']),
            'paths': {int(key.split('_')[1]): path for key, path in
                      pairs.items() if key.startswith('path_')},
            'devids': {int(key.split('_')[1]): int(devid) for key, devid in
                       pairs.items() if key.startswith('devid_')},
        }
        return data


class CreateCloseConfig(RequestConfig):
    COMMAND = 'create_close'

    @classmethod
    def parse_response_text(cls, response_text):
        return {}


class DeleteFileConfig(RequestConfig):
    COMMAND = 'delete'

    @classmethod
    def parse_response_text(cls, response_text):
        print(response_text)
        return {}


class ListKeysConfig(RequestConfig):
    COMMAND = 'list_keys'

    @classmethod
    def parse_response_text(cls, response_text):
        if not response_text or response_text == '':
            return {}
        pairs = parse_response_text(response_text)
        key_count = pairs.pop('key_count')
        next_after = pairs.pop('next_after')
        data = {
            'key_count': int(key_count),
            'next_after': next_after,
            'keys': {int(key.split('_')[1]): file_key for key, file_key in
                     pairs.items()},
        }
        return data


class GetPathsConfig(RequestConfig):
    COMMAND = 'get_paths'

    @classmethod
    def parse_response_text(cls, response_text):
        pairs = parse_response_text(response_text)
        data = {
            'path_count': int(pairs['paths']),
            'paths': {int(key.replace('path', '')): path for key, path in
                      pairs.items() if re.match(r'^path[0-9]+$', key)},
        }
        return data
