from systems.commands.processor import Processor


class Importer(Processor):

    def __init__(self, command, display_only = False):
        super().__init__(command, 'import',
            plugin_key = 'source',
            display_only = display_only
        )
