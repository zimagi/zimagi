from .. import exceptions, utility, transports

import re
import logging


logger = logging.getLogger(__name__)


class DataHTTPSTransport(transports.BaseTransport):

    def handle_request(self, method, url, path, headers, params, decoders):
        if method == 'GET':
            if re.match(r'^(/|/status/?)$', path):
                return self.request_page(url, headers, None, decoders, encrypted = False, disable_callbacks = True)
            return self.request_page(url, headers, params, decoders)
        return self.update_data(method, url, headers, params, decoders)


    def update_data(self, method, url, headers, params, decoders, encrypted = True):
        request, response = self._request(method, url,
            headers = headers,
            params = params,
            encrypted = encrypted
        )
        logger.debug("{} {} request headers: {}".format(method.upper(), url, headers))

        if response.status_code >= 400 and response.status_code != 501:
            raise exceptions.ResponseError(
                utility.format_response_error(response, self.client.cipher if encrypted else None)
            )
        return self.decode_message(request, response, decoders,
            decrypt = encrypted
        )
