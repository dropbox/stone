from __future__ import absolute_import, division, print_function, unicode_literals

import textwrap

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

import os
import unittest
import subprocess
import sys
import shutil
try:
    # Works for Py 3.3+
    from unittest.mock import Mock
except ImportError:
    # See https://github.com/python/mypy/issues/1153#issuecomment-253842414
    from mock import Mock  # type: ignore

from stone.ir import (
    Alias,
    ApiNamespace,
    Boolean,
    Struct,
    StructField,
    Union,
    UnionField,
    Void)
from stone.backends.tsd_types import TSDTypesBackend
from test.backend_test_util import _mock_emit


def _make_backend(target_folder_path, template_path):
    # type: (typing.Text, typing.Text) -> TSDTypesBackend

    args = Mock()
    args.__iter__ = Mock(return_value=iter([template_path, "-i=0"]))

    return TSDTypesBackend(
        target_folder_path=str(target_folder_path),
        args=args
    )


def _make_namespace(ns_name="accounts"):
    # type: (typing.Text) -> ApiNamespace
    ns = ApiNamespace(ns_name)
    struct = _make_struct('User', 'exists_since', ns)
    ns.add_data_type(struct)
    return ns


def _make_struct(struct_name, struct_field_name, namespace):
    # type: (typing.Text, typing.Text, ApiNamespace) -> Struct
    struct = Struct(name=struct_name, namespace=namespace, ast_node=None)
    struct.set_attributes(None, [StructField(struct_field_name, Boolean(), None, None)])
    return struct


def _evaluate_namespace(backend, namespace_list, use_camel_case=False):
    # type: (TSDTypesBackend, typing.List[ApiNamespace], bool) -> typing.Text

    emitted = _mock_emit(backend)
    filename = "types.d.ts"
    backend.split_by_namespace = False
    backend.use_camel_case = use_camel_case
    backend._generate_base_namespace_module(namespace_list=namespace_list,
                                            filename=filename,
                                            extra_args={},
                                            template="""/*TYPES*/""",
                                            exclude_error_types=True)
    result = "".join(emitted)
    return result


class TestTSDTypes(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTSDTypes, self).__init__(*args, **kwargs)
        self.maxDiff = None  # Increase text diff size

    def test__generate_types_single_ns(self):
        # type: () -> None
        backend = _make_backend(target_folder_path="output", template_path="")
        ns = _make_namespace()
        result = _evaluate_namespace(backend, [ns])
        expected = textwrap.dedent("""
        type Timestamp = string;

        namespace accounts {
          export interface User {
            exists_since: boolean;
          }

        }


        """)
        self.assertEqual(result, expected)

    def test__generate_types_empty_ns(self):
        # type: () -> None
        backend = _make_backend(target_folder_path="output", template_path="")
        empty_ns = ApiNamespace("empty_namespace")
        result = _evaluate_namespace(backend, [empty_ns])
        expected = textwrap.dedent("")
        self.assertEqual(result, expected)

    def test__generate_types_with_empty_ns(self):
        # type: () -> None
        backend = _make_backend(target_folder_path="output", template_path="")
        ns = _make_namespace()
        empty_ns = ApiNamespace("empty_namespace")
        result = _evaluate_namespace(backend, [ns, empty_ns])
        expected = textwrap.dedent("""
        type Timestamp = string;

        namespace accounts {
          export interface User {
            exists_since: boolean;
          }

        }


        """)
        self.assertEqual(result, expected)

    def test__generate_types_multiple_ns(self):
        # type: () -> None
        backend = _make_backend(target_folder_path="output", template_path="")
        ns1 = _make_namespace("accounts")
        ns2 = _make_namespace("files")
        result = _evaluate_namespace(backend, [ns1, ns2])
        expected = textwrap.dedent("""
        type Timestamp = string;

        namespace accounts {
          export interface User {
            exists_since: boolean;
          }

        }

        namespace files {
          export interface User {
            exists_since: boolean;
          }

        }


        """)
        self.assertEqual(result, expected)

    def test__generate_types_with_camel_casing(self):
        # type: () -> None
        backend = _make_backend(target_folder_path="output", template_path="")
        ns = _make_namespace()

        struct = _make_struct('UserAddress', 'street_number', ns)
        ns.add_data_type(struct)

        alias = Alias('UserHomeAddress', ns, ast_node=None)
        alias.set_attributes(doc=None, data_type=struct)
        ns.add_alias(alias)

        union = Union('UserLocation', ns, ast_node=None, closed=False)

        union.set_attributes(
            doc=None,
            fields=[
                UnionField(
                    name="zip_code",
                    doc=None,
                    data_type=Void(),
                    ast_node=None
                )
            ],
        )
        ns.add_data_type(union)

        result = _evaluate_namespace(backend, [ns], use_camel_case=True)
        expected = textwrap.dedent("""
        type Timestamp = string;

        namespace accounts {
          export interface User {
            existsSince: boolean;
          }

          export interface UserAddress {
            streetNumber: boolean;
          }

          export interface UserLocationZipCode {
            '.tag': 'zip_code';
          }

          export type UserLocation = UserLocationZipCode;

          export type UserHomeAddress = UserAddress;

        }


        """)
        self.assertEqual(result, expected)


class SpecHelper:
    """
    A helper class which exposes two namespace definitions
    and its corresponding type definitions for testing. The
    types are available as either a declaration or a namespace.
    """

    def __init__(self):
        pass

    _error_types = """
/**
 * An Error object returned from a route.
 */
interface Error<T> {
  // Text summary of the error.
  error_summary: string;
  // The error object.
  error: T;
  // User-friendly error message.
  user_message: UserMessage;
}

/**
 * User-friendly error message.
 */
interface UserMessage {
  // The message.
  text: string;
  // The locale of the message.
  locale: string;
}

"""

    _ns_spec = """\
namespace ns
import ns2
struct A
    "Sample struct doc."
    client_name String
        "Sample field doc."
    client_id Int64
struct B extends ns2.BaseS
    c Bytes
"""

    _ns_spec_types = """{
  /**
   * Sample struct doc.
   */
  export interface A {
    /**
     * Sample field doc.
     */
    clientName: string;
    clientId: number;
  }

  export interface B extends ns2.BaseS {
    c: string;
  }
%s
}
"""

    _ns2_spec = """\
namespace ns2
struct BaseS
    "This is a test."
    z Int64
union_closed BaseU
    z
    x String
alias AliasedBaseU = BaseU
    """

    _ns2_spec_types = """{
  /**
   * This is a test.
   */
  export interface BaseS {
    z: number;
  }

  export interface BaseUZ {
    '.tag': 'z';
  }

  export interface BaseUX {
    '.tag': 'x';
    x: string;
  }

  export type BaseU = BaseUZ | BaseUX;

  export type AliasedBaseU = BaseU;
%s
}
"""

    _timestamp_mapping = 'type Timestamp = string'

    _timestamp_def_formatted = "\n" + "  " + _timestamp_mapping + ";"

    @classmethod
    def get_ns_spec(cls):
        return cls._ns_spec

    @classmethod
    def get_ns_types_as_declaration(cls):
        types = """\nimport * as ns2 from 'ns2';\n""" + (
            ("\ndeclare module 'ns' " + cls._ns_spec_types) % cls._timestamp_def_formatted) + "\n\n"
        return types.replace('namespace', 'declare module')

    @classmethod
    def get_ns2_spec(cls):
        return cls._ns2_spec

    @classmethod
    def get_ns2_types_as_declaration(cls):
        return (("\ndeclare module 'ns2' " + cls._ns2_spec_types
                 ) % cls._timestamp_def_formatted) + "\n\n"

    @classmethod
    def get_all_types_as_namespace(cls):
        types = cls._error_types + "\n" + cls._timestamp_mapping + ";\n" + (
            ("\nnamespace ns " + cls._ns_spec_types) % "") + (
            ("\nnamespace ns2 " + cls._ns2_spec_types) % "") + "\n\n"
        return types


class TestTSDTypesE2E(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestTSDTypesE2E, self).__init__(*args, **kwargs)
        self.maxDiff = None  # Increase text diff size

    def setUp(self):
        self.stone_output_directory = "output"
        if not os.path.exists(self.stone_output_directory):
            os.makedirs(self.stone_output_directory)
        self.template_file_name = "typescript.template"
        template_file_path = "{}/{}".format(self.stone_output_directory, self.template_file_name)
        with open(template_file_path, "w") as template_file:
            template_file.write("/*TYPES*/")

    def tearDown(self):
        # Clear output of stone tool after all tests.
        shutil.rmtree('output')

    def _verify_generated_output(self, filename, expected_namespace_types):
        with open(filename, 'r') as f:
            generated_types = f.read()
            self.assertEqual(generated_types, expected_namespace_types)

    def test_tsd_types_declarations_output(self):
        # Sanity check: stone must be importable for the compiler to work
        __import__('stone')

        # Compile spec by calling out to stone
        p = subprocess.Popen(
            [sys.executable,
             '-m',
             'stone.cli',
             'tsd_types',
             self.stone_output_directory,
             '--',
             self.template_file_name,
             '--exclude-error-types',
             '--use-camel-case',
             '-i=0'],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)
        _, stderr = p.communicate(
            input=(SpecHelper.get_ns_spec() + SpecHelper.get_ns2_spec()).encode('utf-8'))
        if p.wait() != 0:
            raise AssertionError('Could not execute stone tool: %s' %
                                 stderr.decode('utf-8'))

        # one file must be generated per namespace
        expected_ns_output = SpecHelper.get_ns_types_as_declaration()
        self._verify_generated_output('output/ns.d.ts', expected_ns_output)

        expected_ns2_output = SpecHelper.get_ns2_types_as_declaration()
        self._verify_generated_output('output/ns2.d.ts', expected_ns2_output)

    def test_tsd_types_namespace_output(self):
        # Sanity check: stone must be importable for the compiler to work
        __import__('stone')

        output_file_name = "all_types.ts"

        # Compile spec by calling out to stone
        p = subprocess.Popen(
            [sys.executable,
             '-m',
             'stone.cli',
             'tsd_types',
             self.stone_output_directory,
             '--',
             self.template_file_name,
             output_file_name,
             '--use-camel-case',
             '-i=0'],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)
        _, stderr = p.communicate(
            input=(SpecHelper.get_ns_spec() + SpecHelper.get_ns2_spec()).encode('utf-8'))
        if p.wait() != 0:
            raise AssertionError('Could not execute stone tool: %s' %
                                 stderr.decode('utf-8'))

        expected_output = SpecHelper.get_all_types_as_namespace()
        self._verify_generated_output('output/{}'.format(output_file_name), expected_output)


if __name__ == '__main__':
    unittest.main()
