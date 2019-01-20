
class CLITaskMixin(object):
    
    def _parse_args(self, args, overrides = None, lock = False):
        if not lock and overrides:
            overrides = overrides.split(',') if isinstance(overrides, str) else overrides
            arg_count = len(args)

            for index, value in enumerate(overrides):
                if index >= arg_count:
                    args.append(value)
                else:
                    args[index] = value

    def _parse_options(self, options, overrides = None, lock = False):
        if not lock and overrides:
            for key, value in overrides.items():
                options[key] = value    

    def _ssh_exec(self, server, command, args = [], options = {}, sudo = False, ssh = None):
        if not ssh:
            ssh = server.provider.ssh()
        
        if sudo:
            ssh.sudo(command, *args, **options)
        else:
            ssh.exec(command, *args, **options)

