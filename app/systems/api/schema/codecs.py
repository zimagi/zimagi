
from coreapi.codecs.base import BaseCodec


class RichTextCodec(BaseCodec):
    media_type = 'text/*'
    format = 'text'

    def decode(self, bytestring, **options):
        return bytestring.decode('utf-8')