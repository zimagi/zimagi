from systems.command import types, mixins


class RotateCommand(
    types.ServerActionCommand
):
    def parse(self):
        self.parse_network_name('--network')
        self.parse_server_reference(True)

    def exec(self):
        self.set_server_scope()

        def rotate_server(server, state):
            self.data("Rotating SSH keypair for", str(server))
            
            server.provider.rotate_password()
            server.provider.rotate_key()            
            server.save()
        
        self.run_list(self.servers, rotate_server)
