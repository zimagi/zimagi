import re

from systems.plugins.index import BaseProvider
from utility.data import normalize_value


class Provider(BaseProvider("parser", "conditional_value")):
    conditional_pattern = r"^\?\>([^\?]+)\?([^\|]+)\|(.+)$"

    def parse(self, value, config):
        if not isinstance(value, str) or not value.startswith("?>"):
            return value

        if config.conditional_suppress:
            config.conditional_suppress = re.compile(config.conditional_suppress)

        conditional_match = re.search(self.conditional_pattern, value)
        if conditional_match:
            test_element = normalize_value(
                self.command.options.interpolate(conditional_match.group(1).strip(), **config.export())
            )
            true_value = normalize_value(
                self.command.options.interpolate(conditional_match.group(2).strip(), **config.export())
            )
            false_value = normalize_value(
                self.command.options.interpolate(conditional_match.group(3).strip(), **config.export())
            )

            if config.conditional_suppress and (
                (isinstance(test_element, str) and config.conditional_suppress.search(test_element))
                or (isinstance(true_value, str) and config.conditional_suppress.search(true_value))
                or (isinstance(false_value, str) and config.conditional_suppress.search(false_value))
            ):
                value = f"?> {test_element} ? {true_value} | {false_value}"
            else:
                try:
                    test = eval(test_element) if isinstance(test_element, str) else test_element
                except NameError:
                    test = test_element

                if test:
                    try:
                        value = eval(true_value) if isinstance(true_value, str) else true_value
                    except NameError:
                        value = true_value
                else:
                    try:
                        value = eval(false_value) if isinstance(false_value, str) else false_value
                    except NameError:
                        value = false_value
        return value
