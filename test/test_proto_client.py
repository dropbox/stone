from stone.backends.proto_client import ProtoBackend
from stone.ir import (
    ApiNamespace,
    Void,
    Int32,
    Int64,
    Boolean,
    Float32,
    Float64,
    Struct,
    StructField,
    String,
    UInt32,
    UInt64
)

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

    def test_nested_struct(self):

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
                    string\tgiven_name = 0;
                    string\tsurname = 1;
                }

                Name\tname = 0;
                uint64\tage = 1;
            }

        ''')

        self.assertEqual(res, expected)

    def test_struct_with_datatypes(self):
        temp_struc = Struct(u'AllDatas', 'TestStruct2', None)
        temp_struc.set_attributes(None,
        [
            StructField(u'num_int32', Int32(), None, None),
            StructField(u'num_int64', Int64(), None, None),
            StructField(u'num_uint32', UInt32(), None, None),
            StructField(u'num_uint64', UInt64(), None, None),
            StructField(u'num_float32', Float32(), None, None),
            StructField(u'num_float64', Float64(), None, None),
            StructField(u'George', Boolean(), None, None),
            StructField(u'cheese', String(), None, None)
        ])

        ns = ApiNamespace('TestStruct2')
        ns.add_data_type(temp_struc)
        self.backend._generate_types(ns)
        res = self.backend.output_buffer_to_string()

        expected = textwrap.dedent('''\
            message AllDatas {
                int32\tnum_int32 = 0;
                int64\tnum_int64 = 1;
                uint32\tnum_uint32 = 2;
                uint64\tnum_uint64 = 3;
                float\tnum_float32 = 4;
                double\tnum_float64 = 5;
                bool\tGeorge = 6;
                string\tcheese = 7;
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