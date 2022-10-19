from zimagi.collection import Collection

from utility.data import dump_json


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
            msg_prefix + " Key '{}' does not exist in {}.".format(key, ", ".join(data_keys)).strip()
        )


    def assertObjectEqual(self, obj1, obj2, msg_prefix = ''):
        obj1 = obj1.export() if isinstance(obj1, Collection) else obj1
        obj2 = obj2.export() if isinstance(obj2, Collection) else obj2

        def object_equal(inner_obj1, inner_obj2):
            if type(inner_obj1) != type(inner_obj2):
                raise Exception("Type mismatch: {}<{}> != {}<{}>".format(
                    type(inner_obj1),
                    inner_obj1,
                    type(inner_obj2),
                    inner_obj2
                ))
            if isinstance(inner_obj1, dict):
                inner_obj1_keys = inner_obj1.keys()
                inner_obj2_keys = inner_obj2.keys()

                if len(inner_obj1_keys) != len(inner_obj2_keys):
                    raise Exception("Objects have diferent keys: {} != {}".format(
                        inner_obj1_keys,
                        inner_obj2_keys
                    ))
                if sorted(inner_obj1_keys) != sorted(inner_obj2_keys):
                    raise Exception("Objects have diferent keys: {} != {}".format(
                        inner_obj1_keys,
                        inner_obj2_keys
                    ))
                for key, item in inner_obj1.items():
                    object_equal(item, inner_obj2[key])

            elif isinstance(inner_obj1, (list, tuple)):
                if len(inner_obj1) != len(inner_obj2):
                    raise Exception("Object lists are not the same length: {} != {}".format(
                        inner_obj1,
                        inner_obj2
                    ))
                for index, item in enumerate(inner_obj1):
                    object_equal(item, inner_obj2[index])

            elif inner_obj1 != inner_obj2:
                raise Exception("Values not equal: {} != {}".format(
                    inner_obj1,
                    inner_obj2
                ))
        try:
            object_equal(obj1, obj2)
        except Exception as e:
            self.fail(msg_prefix + " Objects '{}' and '{}' are not equal\n{}".format(
                    dump_json(obj1, indent = 2, sort_keys = True),
                    dump_json(obj2, indent = 2, sort_keys = True),
                    e
                ).strip()
            )

    def assertObjectContains(self, whole, part, msg_prefix = ''):
        whole = whole.export() if isinstance(whole, Collection) else whole
        part = part.export() if isinstance(part, Collection) else part

        def object_contains(inner_whole, inner_part):
            if type(inner_whole) != type(inner_part):
                raise Exception("Type mismatch: {}<{}> != {}<{}>".format(
                    type(inner_whole),
                    inner_whole,
                    type(inner_part),
                    inner_part
                ))
            if isinstance(inner_whole, dict):
                inner_whole_keys = inner_whole.keys()
                inner_part_keys = inner_part.keys()

                if len(inner_whole_keys) < len(inner_part_keys):
                    raise Exception("Part has more keys than whole: {} < {}".format(
                        inner_whole_keys,
                        inner_part_keys
                    ))
                if not set(inner_part_keys).issubset(inner_whole_keys):
                    raise Exception("Some keys not in whole: {} not in {}".format(
                        inner_part_keys,
                        inner_whole_keys
                    ))
                for key, item in inner_part.items():
                    object_contains(inner_whole[key], item)

            elif isinstance(inner_whole, (list, tuple)):
                if len(inner_whole) < len(inner_part):
                    raise Exception("Part list is longer than whole: {} < {}".format(
                        inner_whole,
                        inner_part
                    ))
                for index, item in enumerate(inner_part):
                    object_contains(inner_whole[index], item)

            elif inner_whole != inner_part:
                raise Exception("Values not equal: {} != {}".format(
                    inner_whole,
                    inner_part
                ))
        try:
            object_contains(whole, part)
        except Exception as e:
            self.fail(msg_prefix + " Object '{}' does not contain '{}'\n{}".format(
                    dump_json(whole, indent = 2, sort_keys = True),
                    dump_json(part, indent = 2, sort_keys = True),
                    e
                ).strip()
            )
