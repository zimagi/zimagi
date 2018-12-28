from .user import UserActionCommand


class UserTokenActionCommand(UserActionCommand):
    
    def get_token_user(self):
        if self.user_name:
            return self.user
        return self.active_user
