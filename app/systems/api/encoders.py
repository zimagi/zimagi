from rest_framework.utils import encoders


class SafeJSONEncoder(encoders.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except Exception as e:
            return str(obj)
