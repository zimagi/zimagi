
class TestAssertions(object):

    def assertKeyExists(self, key, data, msg_prefix = ''):
        data_keys = list(data.keys()) if data else []
        exists = False

        if isinstance(key, (tuple, list)):
            for item in key:
                if item in data_keys:
                    exists = True
        else:
            exists = key in data_keys

        self.assertTrue(
            exists,
            msg_prefix + "Key '{}' does not exist in {}.".format(key, ", ".join(data_keys)),
        )
