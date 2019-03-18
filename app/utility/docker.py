from utility import shell

import datetime
import docker
import pathlib


class MetaDocker(type):

    @property
    def container_id(self):
        return shell.Shell.capture(('cat', '/proc/1/cpuset')).split('/')[-1]

    def generate_image(self, base_image):
        repository = base_image.split(':')[0]
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(repository, time)

    def create_image(self, id, image_name):
        client = docker.from_env()
        container = client.containers.get(id)
        container.commit(image_name)

    def run_registry(self):
        pathlib.Path('/var/lib/registry').mkdir(mode = 0o700, parents = True, exist_ok = True)

        client = docker.from_env()
        client.containers.run('registry:2',
            name = 'registry',
            network_mode = 'host',
            detach = True,
            restart_policy = {
                "Name": "always",
                "MaximumRetryCount": 10
            },
            mem_limit = '1g',
            ports = {
                5000: 443
            },
            volumes = {
                '/var/lib/registry': {
                    'bind': '/var/lib/registry',
                    'mode': 'rw'
                },
                '-->/certs': {
                    'bind': '/certs',
                    'mode': 'rw'
                },
                '-->/auth': {
                    'bind': '/auth',
                    'mode': 'rw'
                }
            },
            environment = {
                'REGISTRY_HTTP_ADDR': '0.0.0.0:443',
                'REGISTRY_HTTP_TLS_CERTIFICATE': '/certs/domain.crt',
                'REGISTRY_HTTP_TLS_KEY': '/certs/domain.key',
                'REGISTRY_AUTH': 'htpasswd',
                'REGISTRY_AUTH_HTPASSWD_PATH': '/auth/htpasswd',
                'REGISTRY_AUTH_HTPASSWD_REALM': 'Registry Realm'
            }
        )


class Docker(object, metaclass = MetaDocker):
    pass