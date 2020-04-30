import logging
from typing import Dict

import requests
from requests import RequestException

from pymogilefs import backend
from pymogilefs.exceptions import FileNotFoundError
from pymogilefs.response import Response

CHUNK_SIZE = 4096

log = logging.getLogger(__name__)


class Client:
    def __init__(self, trackers, domain):
        self._backend = backend.Backend(trackers)
        self._domain = domain

    def _do_request(self, config, **kwargs):
        return self._backend.do_request(config, **kwargs)

    def _create_open(self, **kwargs):
        return self._do_request(backend.CreateOpenConfig, **kwargs)

    def _create_close(self, **kwargs):
        return self._do_request(backend.CreateCloseConfig, **kwargs)

    def get_file(self, key, timeout=None, zone='default') -> bytes:
        """
        Given a key, returns a filehandle.

        Make sure to consume all the data so the connection could be closed.

        @param key:
        @param timeout:
        @param zone:
        @return:
        """
        paths = self.get_paths(key, zone=zone).data
        if not paths['paths']:
            raise FileNotFoundError(self._domain, key)
        for idx in sorted(paths['paths'].keys()):
            try:
                r = requests.get(paths['paths'][idx], stream=True, timeout=timeout)
                r.raise_for_status()
                return r.raw
            except RequestException as e:
                log.warning('Get file from the url in idx "%s" failed. Try another one.', idx, exc_info=e)
                r.close()
            # TODO: raise proper exception
            # raise  # UnknownFileError
            raise Exception('No usable location to get file.')

    def store_file(self, file_handle, key, _class=None, timeout=None, zone='default') -> Dict:
        """
        Given a key, class, and a filehandle, stores the file contents in MogileFS.

        @param file_handle:
        @param key:
        @param _class:
        @param timeout:
        @param zone:
        @return: path and length
        """
        kwargs = {'domain': self._domain,
                  'key': key,
                  'fid': 0,
                  'multi_dest': 1,
                  'zone': zone}
        if _class is not None:
            kwargs['class'] = _class
        paths = self._create_open(**kwargs).data
        fid = paths['fid']
        for idx in sorted(paths['paths'].keys()):
            path = paths['paths'][idx]
            devid = paths['devids'][idx]
            try:
                r = requests.put(path, data=file_handle, timeout=timeout)
                r.raise_for_status()
            except RequestException as e:
                log.warning('Put file to the url in idx "%s" failed. Try another one.', idx, exc_info=e)
                file_handle.seek(0)
            else:
                # Call create_close to tell the tracker where we wrote the
                # file to and can start replicating it.
                length = file_handle.tell()
                kwargs = {
                    'fid': fid,
                    'domain': self._domain,
                    'key': key,
                    'path': path,
                    'devid': devid,
                    'size': length,
                    'zone': zone
                }
                if _class is not None:
                    kwargs['class'] = _class
                self._create_close(**kwargs)
                return {'path': path, 'length': length}
        # TODO: raise proper exception
        # raise  # UnknownFileError
        raise Exception('No usable location to put file.')

    def delete_file(self, key):
        """
        Delete a key from MogileFS.

        @param key:
        @return:
        """
        return self._do_request(backend.DeleteFileConfig,
                                domain=self._domain,
                                key=key)

    def rename_file(self, key) -> bool:
        """
        Rename file (key) in MogileFS from oldkey to newkey.

        @return: true on success, failure otherwise.
        """
        raise NotImplementedError

    def get_paths(self, key, noverify=True, zone='default', pathcount=2) -> Response:
        """
        Given a key, returns an array of all the locations (HTTP URLs) that the file has been replicated to.

        @param key:
        @param noverify: If the "no verify" option is set, the mogilefsd tracker doesn't verify that the first item returned in the list is up/alive. Skipping that check is faster, so use "noverify" if your application can do it faster/smarter. For instance, when giving Perlbal a list of URLs to reproxy to, Perlbal can intelligently find one that's alive, so use noverify and get out of mod_perl or whatever as soon as possible.
        @param zone: If the zone option is set to 'alt', the mogilefsd tracker will use the alternative IP for each host if available, while constructing the paths.
        @param pathcount: If the pathcount option is set to a positive integer greater than 2, the mogilefsd tracker will attempt to return that many different paths (if available) to the same file. If not present or out of range, this value defaults to 2.
        @return: Response within paths and path_count
        """
        return self._do_request(backend.GetPathsConfig,
                                domain=self._domain,
                                key=key,
                                noverify=1 if noverify else 0,
                                zone=zone,
                                pathcount=pathcount)

    def list_keys(self, prefix=None, after=None, limit=None) -> Response:
        """
        Used to get a list of keys matching a certain prefix.

        @param prefix: specifies what you want to get a list of.
        @param after: the item specified as a return value from this function last time you called it.
        @param limit: defaults to 1000 keys returned.
        @return: Response within key_count, next_after, and keys.
        """
        kwargs = {'domain': self._domain}
        if prefix is not None:
            kwargs['prefix'] = prefix
        if after is not None:
            kwargs['after'] = after
        if limit is not None:
            kwargs['limit'] = limit
        try:
            return self._do_request(backend.ListKeysConfig, **kwargs)
        except Exception as exception:
            if exception.code == 'none_match':
                # Empty result set from this list call should not result
                # in an exception. Return a mocked Mogile response instead.
                response = Response('OK \r\n', backend.ListKeysConfig)
                response.data = {
                    'key_count': 0,
                    'next_after': None,
                    'keys': {},
                }
                return response
            raise exception
