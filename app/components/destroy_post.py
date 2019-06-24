from .destroy import ProfileComponent as BaseProfileComponent

class ProfileComponent(BaseProfileComponent):

    def priority(self):
        return 100
