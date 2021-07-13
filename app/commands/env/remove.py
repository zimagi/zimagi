from systems.commands.index import Command


class Remove(Command('env.remove')):

    def exec(self):
        env_name = self.environment_name if self.environment_name else self.curr_env_name

        self.log_result = False
        self.delete_env(env_name, remove_module_path = self.remove_module_path)
