__all__ = [
    'ApiError', 'ApiRequest', 'ApiResponse', 'Dropbox', 'HttpError',
]

__version__ = '<insert-version-number-here>'

import json
import logging
import os
import pkg_resources
import random
import time

import requests
from requests.adapters import HTTPAdapter

from .exceptions import (
    ApiError,
    BadInputError,
    HttpError,
    InternalServerError,
    RateLimitError
)

class Namespace(object):
    """Container for a namespace of Dropbox API endpoints such as files and
    datastores."""
    def __init__(self, dropbox):
        self._dropbox = dropbox

class ApiResponse(object):
    def __init__(self, obj_segment, binary_segment=None):
        """
        :param dict obj_segment: Contains the top-level struct response.
        :param request.models.Response binary_segment: A response object that
            can be used to stream the raw contents of the response.
        """
        assert isinstance(obj_segment, (dict, type(None))), (
            'obj_segment should be a dict or None'
        )
        self.obj_segment = obj_segment or {}
        self.binary_segment = binary_segment

class Dropbox(object):
    """
    Use this to make requests to the Dropbox API.
    """

    API_VERSION = 2

    DEFAULT_HOST = 'dropbox.com'

    PRESIGNED_VERSION = '2'

    TRUSTED_CERT_FILE = pkg_resources.resource_filename(__name__, 'trusted-certs.crt')

    class Host(object):
        """
        Names of the different hosts used by the Dropbox API.

        :ivar API: Host for general RPCs.
        :ivar API_CONTENT: Host for uploads and downloads.
        :ivar API_NOTIFY: Host for notifications.
        """
        API = 'api'
        API_CONTENT = 'content'
        API_NOTIFY = 'notify'

    class RouteStyle(object):
        """
        Names of the different styles for routes.

        :ivar DOWNLOAD: Download style route.
        :ivar UPLOAD: Upload style route.
        :ivar RPC: RPC style route.
        """
        DOWNLOAD = 'download'
        UPLOAD = 'upload'
        RPC = 'rpc'

    def __init__(self,
                 oauth2_access_token,
                 presigned_credentials=None,
                 max_connections=8,
                 max_retries_on_error=4,
                 user_agent=None):
        """
        Creates a new Dropbox Client.

        :param str oauth2_access_token: OAuth2 access token for making client requests.
        :param tuple presigned_credentials: First element should be the presigned key id,
            and the second element should be the presigned mac key.
        :param int max_connections: Maximum connect pool size.
        :param int max_retries_on_error: On 5** errors, the number of times to retry.
        :param str user_agent: The user agent to use when making requests. This helps
            us identify requests coming from your application. We recommend you use
            the format "AppName/Version".
        """
        self._oauth2_access_token = oauth2_access_token
        self.presigned_credentials = presigned_credentials

        # We only need as many pool_connections as we have unique hostnames.
        http_adapter = HTTPAdapter(pool_connections=4,
                                   pool_maxsize=max_connections)
        # Use a single session for connection re-use.
        self._session = requests.session()
        self._session.mount('http://', http_adapter)
        self._max_retries_on_error = max_retries_on_error

        base_user_agent = 'OfficialDropboxPythonSDK/' + __version__
        if user_agent:
            self._user_agent = '{}/{}'.format(user_agent, base_user_agent)
        else:
            self._user_agent = base_user_agent

        self._logger = logging.getLogger('dropbox')

        self._dbx_hostname = os.environ.get('DBX_HOST', Dropbox.DEFAULT_HOST)
        self._api_hostname = os.environ.get('DBX_API_HOST', 'api.' + self._dbx_hostname)
        self._api_content_hostname = os.environ.get('DBX_API_CONTENT_HOST',
                                                    'api-content.' + self._dbx_hostname)
        self._api_notify_hostname = os.environ.get('DBX_NOTIFY_HOST',
                                                   'api-notify.' + self._dbx_hostname)

        # We import DropboxApi submodules here to prevent circular dependencies
        from .files import Files
        self.files = Files(self)
        from .base_users import BaseUsers
        self.users = BaseUsers(self)

    def request(self,
                host,
                func_name,
                op_style,
                request_params,
                request_binary):
        """
        Makes a request to the Dropbox API.

        :param host: The Dropbox API host to connect to. Use member of
            :class:`Dropbox.Host`.
        :param func_name: The name of the function to invoke.
        :param op_style: The style of the operation. Use member of
            :class:`Dropbox.RouteStyle`.
        :param request_params: Dict of parameters for the function.
        :param request_binary: String or file pointer.
        """
        attempt = 0
        while True:
            self._logger.info('Request to %s', func_name)
            try:
                return self._request_helper(host,
                                            func_name,
                                            op_style,
                                            request_params,
                                            request_binary)
            except (InternalServerError, RateLimitError) as e:
                if isinstance(e, InternalServerError):
                    # Do not count a rate limiting error as an attempt
                    attempt += 1
                if attempt <= self._max_retries_on_error:
                    # Use exponential backoff
                    backoff = 2**attempt * random.random()
                    self._logger.info('HttpError status_code=%s: '
                                      'Retrying in %.1f seconds',
                                      e.status_code, backoff)
                    time.sleep(backoff)
                else:
                    raise

    def _get_hostname_from_host(self, host):
        """
        Returns the appropriate Dropbox Api hostname to query.

        :param host: Use member of :class:`Dropbox.Host`.
        """
        if host == Dropbox.Host.API:
            hostname = self._api_hostname
        elif host == Dropbox.Host.API_CONTENT:
            hostname = self._api_content_hostname
        elif host == Dropbox.Host.API_NOTIFY:
            hostname = self._api_notify_hostname
        else:
            raise ValueError('Unknown value for host: %r' % host)
        return hostname

    def _get_endpoint_url(self, hostname, func_name):
        return 'https://{hostname}/{version}/{func_name}'.format(
            hostname=hostname,
            version=Dropbox.API_VERSION,
            func_name=func_name,
        )

    def _request_helper(self,
                        host,
                        func_name,
                        op_style,
                        request_params,
                        request_binary):
        """See :meth:`request`."""

        hostname = self._get_hostname_from_host(host)
        url = self._get_endpoint_url(hostname, func_name)

        headers = {'Authorization': 'Bearer %s' % self._oauth2_access_token,
                   'User-Agent': self._user_agent}
        encoded_params = json.dumps(request_params)
        body = None
        stream = False

        if op_style == self.RouteStyle.RPC:
            method = 'POST'
            headers['Content-Type'] = 'application/json'
            body = encoded_params
        elif op_style == self.RouteStyle.DOWNLOAD:
            method = 'GET'
            headers['Dropbox-API-Arg'] = encoded_params
            stream = True
        elif op_style == self.RouteStyle.UPLOAD:
            method = 'POST'
            headers['Content-Type'] = 'application/octet-stream'
            headers['Dropbox-API-Arg'] = encoded_params
            body = request_binary
        else:
            raise ValueError('Unknown operation style: %r' % op_style)

        r = self._session.request(method,
                                  url,
                                  headers=headers,
                                  data=body,
                                  stream=stream,
                                  #verify=False,
                                  #cert=Dropbox.TRUSTED_CERT_FILE,
                                  )

        # Only 400 and 500 status codes have text bodies, everything else is JSON.
        if r.status_code >= 500:
            raise InternalServerError(r.status_code, r.text)
        elif r.status_code == 400:
            raise BadInputError(r.text)
        elif r.status_code == 409:
            try:
                body = r.json()
            except ValueError:
                raise ApiError('cannot_parse_json', r.text)
            if isinstance(body, dict):
                assert len(body.keys()) == 1, 'Error body should have 1 key'
                raise ApiError(body.keys()[0], body.values()[0])
            else:
                raise ApiError(body, None)
        elif r.status_code == 429:
            # TODO: Specify backoff in the body if the server passes it back.
            raise RateLimitError()
        elif 200 <= r.status_code <= 299:
            if op_style == self.RouteStyle.DOWNLOAD:
                raw_resp = r.headers['dropbox-api-result']
            else:
                raw_resp = r.content.decode('utf-8')
            try:
                resp = json.loads(raw_resp)
            except ValueError:
                raise ApiError('cannot_parse_json', raw_resp)
            if op_style == self.RouteStyle.DOWNLOAD:
                return ApiResponse(resp, r)
            else:
                return ApiResponse(resp)
        else:
            raise HttpError(r.status_code, r.json())

    def get_presigned_credentials(self):
        raise NotImplemented

    def presigned_url(self,
                      host,
                      func_name,
                      request_params,
                      expires,
                      omitted_params,
                      ):
        """
        Makes request to the Dropbox API.

        :param host: The Dropbox API host to connect to. Use Dropbox.Host.*.
        :param func_name: The name of the function to invoke.
        :param request_params: Dict of parameters for the function.
        :param expires: The UNIX time (seconds) when this signature expires.
        :param omitted_params: List of parameters to omit from the signature.
        """
        raise NotImplemented
