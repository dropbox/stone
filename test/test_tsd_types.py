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
    ApiNamespace,
    Boolean,
    Struct,
    StructField)
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
    struct = _make_struct('User', 'exists', ns)
    ns.add_data_type(struct)
    return ns


def _make_struct(struct_name, struct_field_name, namespace):
    # type: (typing.Text, typing.Text, ApiNamespace) -> Struct
    struct = Struct(name=struct_name, namespace=namespace, ast_node=None)
    struct.set_attributes(None, [StructField(struct_field_name, Boolean(), None, None)])
    return struct


def _evaluate_namespace(backend, namespace_list):
    # type: (TSDTypesBackend, typing.List[ApiNamespace]) -> typing.Text

    emitted = _mock_emit(backend)
    filename = "types.d.ts"
    backend.split_by_namespace = False
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
        namespace accounts {
          export interface User {
            exists: boolean;
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
        namespace accounts {
          export interface User {
            exists: boolean;
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
        namespace accounts {
          export interface User {
            exists: boolean;
          }

        }

        namespace files {
          export interface User {
            exists: boolean;
          }

        }


        """)
        self.assertEqual(result, expected)


error_types = """
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

test_spec = """\
namespace ns
import ns2
struct A
    "Sample struct doc."
    a String
        "Sample field doc."
    b Int64
struct B extends ns2.BaseS
    c Bytes
"""

test_types = """
declare namespace ns {
  /**
   * Sample struct doc.
   */
  export interface A {
    /**
     * Sample field doc.
     */
    a: string;
    b: number;
  }

  export interface B extends ns2.BaseS {
    c: string;
  }
%s
}
"""

test_ns2_spec = """\
namespace ns2
struct BaseS
    "This is a test."
    z Int64
union_closed BaseU
    z
    x String
alias AliasedBaseU = BaseU
"""

test_ns2_types = """
declare namespace ns2 {
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

timestamp_definition = "\n" + "  type Timestamp = string;"


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

    def _verify_output_generated(self, filename, expected_namespace_types):
        with open(filename, 'r') as f:
            generated_types = f.read()
            self.assertEqual(generated_types, expected_namespace_types)

    def test_tsd_types_file_output(self):
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
             '--exclude_error_types',
             '-i=0'],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)
        _, stderr = p.communicate(
            input=(test_spec + test_ns2_spec).encode('utf-8'))
        if p.wait() != 0:
            raise AssertionError('Could not execute stone tool: %s' %
                                 stderr.decode('utf-8'))

        # one file must be generated per namespace
        expected_ns_output = """\n///<reference path='ns2.d.ts' />\n""" + (
            test_types % timestamp_definition) + "\n\n"
        self._verify_output_generated('output/ns.d.ts', expected_ns_output)

        expected_ns2_output = (test_ns2_types % timestamp_definition) + "\n\n"
        self._verify_output_generated('output/ns2.d.ts', expected_ns2_output)

    def test_tsd_types_modules_output(self):
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
             '-i=0'],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)
        _, stderr = p.communicate(
            input=(test_spec + test_ns2_spec).encode('utf-8'))
        if p.wait() != 0:
            raise AssertionError('Could not execute stone tool: %s' %
                                 stderr.decode('utf-8'))

        expected_output = error_types + "\ntype Timestamp = string;\n" + (
            test_types.replace('declare ', '') % "") + (
            test_ns2_types.replace('declare ', '') % "") + "\n\n"
        self._verify_output_generated('output/{}'.format(output_file_name), expected_output)


if __name__ == '__main__':
    unittest.main()
