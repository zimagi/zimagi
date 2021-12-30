from . import exceptions, utility, schema

import urllib


class BaseAPIClient(object):

    def __init__(self, host, port, transports, decoders):
        self.host = host
        self.port = port
        self.base_url = utility.get_service_url(host, port)
        self.transports = transports
        self.decoders = decoders


    def _determine_transport(self, url):
        url_components = urllib.parse.urlparse(url)
        scheme = url_components.scheme.lower()
        netloc = url_components.netloc

        if not scheme:
            raise exceptions.CommandClientError("URL missing scheme '{}'.".format(url))
        if not netloc:
            raise exceptions.CommandClientError("URL missing hostname '{}'.".format(url))

        for transport in self.transports:
            if scheme in transport.schemes:
                return transport

        raise exceptions.CommandClientError("Unsupported URL scheme '{}'.".format(scheme))


    def _get(self, url, params = None):
        if params is None:
            params = {}

        link = schema.Link(url, action = 'get')
        return self._determine_transport(link.url).transition(
            link,
            self.decoders,
            params = params
        )
