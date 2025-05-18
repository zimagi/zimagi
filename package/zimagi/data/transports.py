import logging
import re

from .. import exceptions, transports, utility

logger = logging.getLogger(__name__)


class DataHTTPTransport(transports.BaseTransport):
    def handle_request(self, method, url, path, headers, params, decoders):
        if method == "GET":
            if re.match(r"^/status/?$", path):
                return self.request_page(
                    url, headers, None, decoders, encrypted=False, use_auth=False, disable_callbacks=True
                )
            if not path or path == "/" or path.startswith("/schema/"):
                return self.request_page(
                    url, headers, None, decoders, encrypted=False, use_auth=True, disable_callbacks=True
                )
            return self.request_page(url, headers, params, decoders, encrypted=True, use_auth=True)
        return self.update_data(method, url, headers, params, decoders)

    def update_data(self, method, url, headers, params, decoders, encrypted=True):
        request, response = self._request(
            method,
            url,
            headers={"Content-type": "application/json", **headers},
            params=utility.dump_json(params),
            encrypted=encrypted,
            use_auth=True,
        )
        logger.debug(f"{method.upper()} {url} request headers: {headers}")

        if response.status_code >= 400:
            error = utility.format_response_error(response, self.client.cipher if encrypted else None)
            raise exceptions.ResponseError(error["message"], response.status_code, error["data"])
        return self.decode_message(request, response, decoders, decrypt=encrypted)
