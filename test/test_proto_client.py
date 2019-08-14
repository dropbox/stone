from stone.backends.proto_client import ProtoBackend
from stone.ir import ApiNamespace, Void, Int32, Struct, StructField, String, UInt64

# MYPY = False
# if MYPY:
#     import typing

import textwrap
import unittest

class TestGeneratedProtoClient(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGeneratedProtoClient, self).__init__(*args, **kwargs)
        self.backend = ProtoBackend(
            target_folder_path='../dev_work',
            args=None
        )

    def test_struct(self):

        nest_struc = Struct(u'Name', "TestStruct", None)

        nest_struc.set_attributes(None,
        [
            StructField(u'given_name', String(), None, None),
            StructField(u'surname', String(), None, None)
        ])

        parent_struc = Struct(u'Person', "TestStruct", None)

        parent_struc.set_attributes(None,
        [
            StructField(u'name',nest_struc, None, None),
            StructField(u'age', UInt64(), None, None)

        ])



        ns = ApiNamespace('TestStruct')
        ns.add_data_type(parent_struc)
        ns.add_data_type(nest_struc)

        self.backend._generate_types(ns)
        res = self.backend.output_buffer_to_string()

        expected = textwrap.dedent('''\
            message Person {
                message Name {
                    String given_name = 0;
                    String surname = 1;
                }

                Name name = 0;
                UInt64 age = 1;
            }

        ''')

        self.assertEqual(res, expected)

    def test_package(self):
        ns = ApiNamespace('TestPkg')
        self.backend._create_package(ns.name)
        res = self.backend.output_buffer_to_string()
        expected = textwrap.dedent('package TestPkg;\n\n')

        self.assertEqual(res, expected)
unittest.main()