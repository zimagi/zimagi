from systems.api import response as shared_responses


class EncryptedResponse(shared_responses.EncryptedResponse):
    api_type = 'command_api'

class EncryptedCSVResponse(shared_responses.EncryptedCSVResponse):
    api_type = 'command_api'
