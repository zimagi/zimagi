from systems.commands.index import Command


class Rotate(Command("user.rotate")):
    def exec(self):
        user = self.user if self.user_key else self.active_user
        token = self._user.generate_token()

        user.set_password(token)
        user.save()

        self.silent_data("name", user.name)
        self.data(f"User {user.name} token:", token, "token")
