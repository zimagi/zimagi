from .. import transports

import re
import logging


logger = logging.getLogger(__name__)


class DataHTTPSTransport(transports.BaseTransport):

    def handle_request(self, url, path, headers, params, decoders):
        if re.match(r'^(/|/status/?)$', path):
            return self.request_page(url, headers, None, decoders, encrypted = False, disable_callbacks = True)
        return self.request_page(url, headers, params, decoders, encrypted = True)
