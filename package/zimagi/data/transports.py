from requests.exceptions import ConnectionError

from .. import exceptions, transports

import logging


logger = logging.getLogger(__name__)


class DataHTTPSTransport(transports.BaseTransport):

    def transition(self, link, decoders, params = None):
        params = self.get_params(link, params)
        url = self.get_url(link.url, params.path)
        headers = self.get_headers(url, decoders)
        headers.update(self._headers)

        if link.action == 'get':
            try:
                return self.request_page(url, headers, params, decoders)

            except ConnectionError as error:
                raise exceptions.CommandConnectionError(error)


    def _decode_result_error(self, result, response):
        return result
