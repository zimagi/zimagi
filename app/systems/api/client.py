
from django.conf import settings
from django.core.management.base import CommandError

from coreapi import Client
from coreapi import codecs
from coreapi import exceptions

from systems.api import auth, transports
from utility.common import flatten

import re
import json


class API(object):
  
    def __init__(self, host, port, token, message_callback = None):
        self.base_url = self.get_service_url(host, port)
        self.client = Client(
            decoders = [
                codecs.CoreJSONCodec(), # application/vnd.coreapi+json
                codecs.JSONCodec()      # application/json
            ], 
            transports = [
                transports.CommandHTTPSTransport(
                    auth = auth.EncryptedClientTokenAuthentication(
                        token = token,
                        scheme = 'Token',
                        domain = '*'
                    ),
                    message_callback = message_callback
                ) # https only
            ]
        )
        self.schema = self.client.get(self.base_url)


    def get_service_url(self, host, port):
        return "https://{}:{}/".format(host, port)


    def _normalize_data(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._normalize_data(value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                data[index] = self._normalize_data(value)
        else:
            # Scalar value
            if isinstance(data, str) and len(data) == 0:
                data = None
        
        return data

    def _format_params(self, params):
        params = self._normalize_data(params)

        for key, value in params.items():
            if isinstance(value, dict):
                params[key] = json.dumps(value)
            elif isinstance(value, (list, tuple)):
                params[key] = json.dumps(list(value))

        return params


    def execute(self, action, params = {}):
        try:
            action = action.split(' ') if isinstance(action, str) else action
            params = self._format_params(params)
            return self.client.action(self.schema, action, params = params)
        
        except exceptions.ErrorMessage as error:
            raise CommandError("API request error: {}\n".format(error))
