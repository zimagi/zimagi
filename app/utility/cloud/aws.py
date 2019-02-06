

class AWSServiceMixin(object):

    def aws_credentials(self, config = {}):
        try:
            config['access_key'] = self.command.get_config('aws_access_key', required = True).strip()
            config['secret_key'] = self.command.get_config('aws_secret_key', required = True).strip()
    
        except Exception:
            self.command.error("To use AWS provider you must have 'aws_access_key' and 'aws_secret_key' environment configurations; see: config set")
        
        return config
