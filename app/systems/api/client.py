
from django.conf import settings
from django.core.management.base import CommandError

from coreapi import Client
from coreapi import auth
from coreapi import codecs
from coreapi import transports
from coreapi import exceptions

from systems.api.schema import codecs as app_codecs
from utility.common import flatten

import re
import json


class API(object):
  
    def __init__(self, host, port, token):
        self.base_url = self.get_service_url(host, port)
        self.client = Client(
            decoders = [
                codecs.CoreJSONCodec(),    # application/vnd.coreapi+json
                app_codecs.RichTextCodec() # text/richtext
            ], 
            transports = [
                transports.HTTPTransport(
                    auth = auth.TokenAuthentication(
                        token = token,
                        scheme = 'Token',
                        domain = '*'
                    )
                ) # http, https
            ]
        )
        self.schema = self.client.get(self.base_url)


    def get_service_url(self, host, port):
        protocol = 'http' if host == 'localhost' else 'https'
        return "{}://{}:{}/".format(protocol, host, port)

    def normalize_params(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.normalize_params(value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                data[index] = self.normalize_params(value)
        else:
            # Scalar value
            if isinstance(data, str) and len(data) == 0:
                data = None
        
        return data


    def execute(self, action, params = {}):
        try:
            action = action.split(' ') if isinstance(action, str) else action
            params = self.normalize_params(params)
            return self.client.action(self.schema, action, params=params)
        
        except exceptions.ErrorMessage as error:
            raise CommandError("API request error: {}\n".format(error))
