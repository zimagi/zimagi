from systems.plugins.index import BasePlugin
from utility.data import get_identifier, dump_json

import copy
import billiard as multiprocessing


class SummaryResult(object):

    def __init__(self, text, prompt_tokens, output_tokens, cost=None):
        self.text = text
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens
        self.total_tokens = prompt_tokens + output_tokens
        self.cost = cost

    def __str__(self):
        return dump_json(self.__dict__, indent=2)

    def __repr__(self):
        return self.__str__()

    def export(self):
        return copy.deepcopy(self.__dict__)


class BaseProvider(BasePlugin("summarizer")):

    lock = multiprocessing.Lock()

    def __init__(self, type, name, command, init=True, **options):
        super().__init__(type, name, command)
        self.import_config(options)

        self.identifier = self._get_identifier(init)

        with self.lock:
            self.initialize(self, init)

    @classmethod
    def initialize(cls, instance, init):
        raise NotImplementedError("Class initialize method required by all subclasses")

    def _get_identifier(self, init):
        return get_identifier(["1" if init else "0", self.name, self.field_device])

    def get_max_context(self):
        raise NotImplementedError(
            "Class get_max_context method required by all subclasses"
        )

    def get_chunk_length(self):
        raise NotImplementedError(
            "Class get_chunk_length method required by all subclasses"
        )

    def get_token_count(self, text):
        raise NotImplementedError(
            "Class get_token_count method required by all subclasses"
        )

    def _get_prompt(self, text="", prompt="", persona="", output_format=""):
        raise NotImplementedError("Class _get_prompt method required by all subclasses")

    def get_prompt_token_count(self, prompt="", persona="", output_format=""):
        token_count = 0
        token_padding = 10

        for message in ensure_list(
            self._get_prompt("", prompt, persona, output_format)
        ):
            token_count += self.get_token_count(message) + token_padding

        return token_count

    def summarize(self, text, **config):
        raise NotImplementedError("Class summarize method required by all subclasses")
