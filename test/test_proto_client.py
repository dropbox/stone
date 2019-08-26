from __future__ import unicode_literals
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

import textwrap
import unittest

class TestGeneratedProtoClient(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGeneratedProtoClient, self).__init__(*args, **kwargs)
        self.backend = ProtoBackend(
            target_folder_path='output',
            args=['-m', 'output']
        )

    def test_package(self):
        ns = ApiNamespace('TestPkg')
        self.backend._create_package(ns.name)
        res = self.backend.output_buffer_to_string()
        expected = textwrap.dedent('''\
            syntax = "proto3";
            package TestPkg;
            import dropbox/proto/api_proxy/service_extensions.proto;\n\n''')

        self.assertEqual(res, expected)

    def test_nested_struct(self):

        nest_struc = Struct('Name', "TestStruct", None)

        nest_struc.set_attributes(None,
        [
            StructField('given_name', String(), None, None),
            StructField('surname', String(), None, None)
        ])

        parent_struc = Struct('Person', "TestStruct", None)

        parent_struc.set_attributes(None,
        [
            StructField('name',nest_struc, None, None),
            StructField('age', UInt64(), None, None)

        ])

        ns = ApiNamespace('TestStruct')
        ns.add_data_type(nest_struc)
        ns.add_data_type(parent_struc)

        self.backend._generate_types(ns)
        res = self.backend.output_buffer_to_string()

        expected = textwrap.dedent('''\
            message Name {
                string given_name\t= 0;
                string surname\t= 1;
            }

            message Person {
                Name name\t= 0;
                uint64 age\t= 1;
            }

        ''')

        self.assertEqual(res, expected)

    def test_struct_with_datatypes(self):
        temp_struc = Struct('AllDatas', 'TestStruct2', None)
        temp_struc.set_attributes(None,
        [
            StructField('num_int32', Int32(), None, None),
            StructField('num_int64', Int64(), None, None),
            StructField('num_uint32', UInt32(), None, None),
            StructField('num_uint64', UInt64(), None, None),
            StructField('num_float32', Float32(), None, None),
            StructField('num_float64', Float64(), None, None),
            StructField('George', Boolean(), None, None),
            StructField('cheese', String(), None, None)
        ])

        ns = ApiNamespace('TestStruct2')
        ns.add_data_type(temp_struc)
        self.backend._generate_types(ns)
        res = self.backend.output_buffer_to_string()

        expected = textwrap.dedent('''\
            message AllDatas {
                int32 num_int32\t= 0;
                int64 num_int64\t= 1;
                uint32 num_uint32\t= 2;
                uint64 num_uint64\t= 3;
                float num_float32\t= 4;
                double num_float64\t= 5;
                bool George\t= 6;
                string cheese\t= 7;
            }

        ''')

        self.assertEqual(res, expected)

    def test_struct_comp(self):
        name_struc = Struct('Name', 'TestStruct', None)
        name_struc.set_attributes(None,
        [
            StructField('given_name', String(), None, None),
            StructField('surname', String(), None, None)
        ])

        dob_struc = Struct('DOB', 'TestStruct', None)
        dob_struc.set_attributes(None,
        [
            StructField('month', Int32(), None, None),
            StructField('day', Int32(), None, None),
            StructField('year', Int32(), None, None)
        ])

        person1_struc = Struct('Person1', "TestStruct", None)

        person1_struc.set_attributes(None,
        [
            StructField('name',name_struc, None, None),
            StructField('age', UInt64(), None, None)
        ])

        person2_struc = Struct('Person2', "TestStruct", None)

        person2_struc.set_attributes(None,
        [
            StructField('name',name_struc, None, None),
            StructField('dob', dob_struc, None, None)
        ])

        ns = ApiNamespace('TestStruct')
        ns.add_data_type(dob_struc)
        ns.add_data_type(name_struc)
        ns.add_data_type(person1_struc)
        ns.add_data_type(person2_struc)

        self.backend._generate_types(ns)
        res = self.backend.output_buffer_to_string()

        expected = textwrap.dedent('''\
           message DOB {
               int32 month\t= 0;
               int32 day\t= 1;
               int32 year\t= 2;
           }

           message Name {
               string given_name\t= 0;
               string surname\t= 1;
           }

           message Person1 {
               Name name\t= 0;
               uint64 age\t= 1;
           }

           message Person2 {
               Name name\t= 0;
               DOB dob\t= 1;
           }

        ''')

        self.assertEqual(res, expected)
unittest.main()