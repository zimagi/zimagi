
import boto3
import requests
import string
import random


class AWSServiceMixin(object):

    def _init_session(self):
        if not getattr(self, 'session', None):
            try:
                access_key = self.command.required_config('aws_access_key').strip()
                secret_key = self.command.required_config('aws_secret_key').strip()
            except Exception:
                self.command.error("To use AWS provider you must have 'aws_access_key' and 'aws_secret_key' environment configurations; see: config set")

            self.session = boto3.Session(
                aws_access_key_id = access_key,
                aws_secret_access_key = secret_key
            )  

    def ec2(self, region = 'us-east-1'):
        self._init_session()
        return self.session.client('ec2', region_name = region)

    def efs(self, region = 'us-east-1'):
        self._init_session()
        return self.session.client('efs', region_name = region)


    def regions(self, service):
        if not getattr(self, '_regions', None):
            regions = service().describe_regions()
            self._regions = []

            for region in regions['Regions']:
                self._regions.append(region['RegionName'])

        return self._regions

    def validate_region(self, name, value, errors, service):
        regions = self.regions(service)
        
        if not value in regions:
            errors.append("Region '{}' is not available, consider: {}".format(value, ", ".join(regions)))

    def zones(self, service, region):
        if not getattr(self, '_zones', None) or region not in self._zones:
            self._zones = getattr(self, '_zones', {})
            self._zones[region] = []

            zones = service(region).describe_availability_zones()
        
            for zone in zones['AvailabilityZones']:
                if zone['State'] == 'available':
                    self._zones[region].append(zone['ZoneName'])
        
        return self._zones[region]

    def validate_zone(self, name, value, errors, service):
        if self.config['region']:
            zones = self.zones(service, self.config['region'])
        
            if not value in zones:
                errors.append("Zone '{}' is not available, consider: {}".format(value, ", ".join(zones)))
        else:
            errors.append("Region is required to validate availability zone")            


    def get_external_ip(self):
        return requests.get('https://api.ipify.org').text


    def create_token(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(32))
