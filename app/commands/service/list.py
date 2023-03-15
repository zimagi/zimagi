from systems.commands.index import Command


class List(Command('service.list')):

    def exec(self):
        service_map = [[ 'Service', 'Status' ]]

        self.success('Available services:')
        for service_name in self.manager.service_names:
            data = self.manager.get_service(service_name, create = False)
            service_map.append([
                service_name,
                data['service'].status if data and 'service' in data else 'not running'
            ])
        self.table(service_map, 'services')
