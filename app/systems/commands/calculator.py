from systems.commands.processor import Processor


class Calculator(Processor):
    def __init__(self, command, display_only=False, reset=False):
        super().__init__(
            command,
            "calculation",
            display_only=display_only,
        )
        self.reset = reset

    def provider_process(self, name, spec):
        self.command.get_provider(self.plugin_key, spec[self.plugin_key], name, spec).process(self.reset)
