from utility.cloud.aws import AWSServiceMixin
from .base import BaseFederationProvider


class AWS(AWSServiceMixin, BaseFederationProvider):
  
    def initialize_terraform(self, instance, created, pair):
        namespace = self._peer_namespace(pair)
        source = pair[0]
        peer = pair[1]
        
        instance.config.setdefault(namespace, {})
        self.aws_credentials(instance.config[namespace])        
        
        try:
            instance.config[namespace]['region'] = source.config['region']
            instance.config[namespace]['vpc_id'] = source.variables['vpc_id']
            instance.config[namespace]['peer_region'] = peer.config['region']
            instance.config[namespace]['peer_vpc_id'] = peer.variables['vpc_id']
        
        except KeyError as e:
            self.command.warning("Could not access {} within {} peering connection".format(str(e), instance.name))

        super().initialize_terraform(instance, created, pair)

    def finalize_terraform(self, instance, pair):
        namespace = self._peer_namespace(pair)

        instance.config.setdefault(namespace, {})
        self.aws_credentials(instance.config[namespace])

        super().finalize_terraform(instance, pair)
