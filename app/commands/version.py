from django.conf import settings
from systems.commands.index import Command


class Version(Command("version")):
    def exec(self):
        if not settings.API_EXEC:
            host = self.get_host()
            version_info = [[self.key_color("Client version"), self.value_color(self.get_version())]]
            if host:
                response = self.exec_remote(host, "version", display=False)

                version_info.extend(
                    [
                        [self.key_color("Host version"), self.value_color(response["host_version"])],
                    ]
                )
            self.table(version_info, "version_info")
        else:
            self.silent_data("host_version", self.get_version())
