from systems.commands.index import Command

import oyaml


class Get(Command('service.get')):

    def exec(self):
        service_spec = self.manager.get_service_spec(self.service_name)
        self.data(self.key_color(self.service_name), "\n\n" + oyaml.dump(service_spec), 'service')

        data = self.manager.get_service(self.service_name, restart = False, create = False)
        if data:
            status = data['service'].status if 'service' in data else 'not running'
            self.data('Status', status, 'status')

            ports = data['ports'] if 'ports' in data else 'none'
            self.data('Ports', "\n\n" + oyaml.dump(ports), 'ports')
