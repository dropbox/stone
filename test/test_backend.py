#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from stone.ir import (
    Alias,
    ApiNamespace,
    ApiRoute,
    List,
    Boolean,
    String,
    Struct,
    StructField,
    resolve_aliases
)
from stone.frontend.frontend import (
    specs_to_ir
)
from stone.backend import (
    remove_aliases_from_api,
    CodeBackend
)

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

# Hack to get around some of Python 2's standard library modules that
# accept ascii-encodable unicode literals in lieu of strs, but where
# actually passing such literals results in errors with mypy --py2. See
# <https://github.com/python/typeshed/issues/756> and
# <https://github.com/python/mypy/issues/2536>.
import importlib
argparse = importlib.import_module(str('argparse'))  # type: typing.Any

class _Tester(CodeBackend):
    """A no-op backend used to test helper methods."""
    def generate(self, api):
        pass

class _TesterCmdline(CodeBackend):
    cmdline_parser = argparse.ArgumentParser()
    cmdline_parser.add_argument('-v', '--verbose', action='store_true')
    def generate(self, api):
        pass

class TestBackend(unittest.TestCase):
    """
    Tests the interface exposed to backends.
    """

    def test_api_namespace(self):
        ns = ApiNamespace('files')
        a1 = Struct('A1', None, ns)
        a1.set_attributes(None, [StructField('f1', Boolean(), None, None)])
        a2 = Struct('A2', None, ns)
        a2.set_attributes(None, [StructField('f2', Boolean(), None, None)])
        l1 = List(a1)
        s = String()
        route = ApiRoute('test/route', 1, None)
        route.set_attributes(None, None, l1, a2, s, None)
        ns.add_route(route)

        # Test that only user-defined types are returned.
        route_io = ns.get_route_io_data_types()
        self.assertIn(a1, route_io)
        self.assertIn(a2, route_io)
        self.assertNotIn(l1, route_io)
        self.assertNotIn(s, route_io)

    def test_code_backend_helpers(self):
        t = _Tester(None, [])
        self.assertEqual(t.filter_out_none_valued_keys({}), {})
        self.assertEqual(t.filter_out_none_valued_keys({'a': None}), {})
        self.assertEqual(t.filter_out_none_valued_keys({'a': None, 'b': 3}), {'b': 3})

    def test_code_backend_basic_emitters(self):
        t = _Tester(None, [])

        # Check basic emit
        t.emit('hello')
        self.assertEqual(t.output_buffer_to_string(), 'hello\n')
        t.clear_output_buffer()

        # Check that newlines are disallowed in emit
        self.assertRaises(AssertionError, lambda: t.emit('hello\n'))

        # Check indent context manager
        t.emit('hello')
        with t.indent():
            t.emit('world')
            with t.indent():
                t.emit('!')
        expected = """\
hello
    world
        !
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        # --------------------------------------------------------
        # Check text wrapping emitter

        with t.indent():
            t.emit_wrapped_text('Colorless green ideas sleep furiously',
                                prefix='$', initial_prefix='>',
                                subsequent_prefix='|', width=13)
        expected = """\
    $>Colorless
    $|green
    $|ideas
    $|sleep
    $|furiously
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

    def test_code_backend_list_gen(self):
        t = _Tester(None, [])

        t.generate_multiline_list(['a=1', 'b=2'])
        expected = """\
(a=1,
 b=2)
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1', 'b=2'], 'def __init__', after=':')
        expected = """\
def __init__(a=1,
             b=2):
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1', 'b=2'], before='function_to_call', compact=False)
        expected = """\
function_to_call(
    a=1,
    b=2,
)
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1', 'b=2'], 'function_to_call',
                                  compact=False, skip_last_sep=True)
        expected = """\
function_to_call(
    a=1,
    b=2
)
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1', 'b=2'], 'def func', ':',
                                  compact=False, skip_last_sep=True)
        expected = """\
def func(
    a=1,
    b=2
):
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1'], 'function_to_call', compact=False)
        expected = 'function_to_call(a=1)\n'
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list(['a=1'], 'function_to_call', compact=True)
        expected = 'function_to_call(a=1)\n'
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list([], 'function_to_call', compact=False)
        expected = 'function_to_call()\n'
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        t.generate_multiline_list([], 'function_to_call', compact=True)
        expected = 'function_to_call()\n'
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        # Test delimiter
        t.generate_multiline_list(['String'], 'List', delim=('<', '>'), compact=True)
        expected = 'List<String>\n'
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

    def test_code_backend_block_gen(self):
        t = _Tester(None, [])

        with t.block('int sq(int x)', ';'):
            t.emit('return x*x;')
        expected = """\
int sq(int x) {
    return x*x;
};
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        with t.block('int sq(int x)', allman=True):
            t.emit('return x*x;')
        expected = """\
int sq(int x)
{
    return x*x;
}
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

        with t.block('int sq(int x)', delim=('<', '>'), dent=8):
            t.emit('return x*x;')
        expected = """\
int sq(int x) <
        return x*x;
>
"""
        self.assertEqual(t.output_buffer_to_string(), expected)
        t.clear_output_buffer()

    def test_backend_cmdline(self):
        t = _TesterCmdline(None, ['-v'])
        self.assertTrue(t.args.verbose)

    def test_resolve_aliases(self):
        first_alias = Alias(None, None, None)
        first_alias.data_type = String()
        returned_alias = resolve_aliases(first_alias)

        # Test that single-level alias chain resolves
        self.assertEqual(returned_alias, first_alias)
        self.assertIsInstance(returned_alias.data_type, String)

        first_alias = Alias(None, None, None)
        second_alias = Alias(None, None, None)
        first_alias.data_type = second_alias
        second_alias.data_type = String()

        # Test that a two-level alias chain resolves
        returned_alias = resolve_aliases(first_alias)
        self.assertEqual(returned_alias, first_alias)
        self.assertIsInstance(first_alias.data_type, String)
        self.assertIsInstance(second_alias.data_type, String)

    def test_preserve_aliases_from_api(self):
        spec = """\
namespace preserve_alias

route eval(TestStruct, TestResult, TestError)

alias NamespaceId = String(pattern="[-_0-9a-zA-Z:]+")
alias SharedFolderId = NamespaceId
alias PathRootId = SharedFolderId

struct TestStruct
    field1 PathRootId

alias StructAlias = TestStruct

struct TestResult
    field1 PathRootId

union TestError
    test PathRootId
"""

        api = specs_to_ir(
            [(None, spec)]
        )
        
        # Ensure namespace exists
        self.assertEqual(len(api.namespaces), 1)
        self.assertTrue('preserve_alias' in api.namespaces)

        ns = api.namespaces['preserve_alias']
    
        aliases = {
            alias._name: alias for alias in ns.aliases 
        }
        data_types = {
            data_type._name: data_type for data_type in ns.data_types
        }

        # Ensure aliases are in the namespace
        self.assertTrue('NamespaceId' in aliases)
        self.assertTrue('SharedFolderId' in aliases)
        self.assertTrue('PathRootId' in aliases)
        self.assertTrue('StructAlias' in aliases)

        # Ensure aliases resolve to proper types
        self.assertIsInstance(aliases['NamespaceId'].data_type, String)
        self.assertIsInstance(aliases['SharedFolderId'].data_type, Alias)
        self.assertIsInstance(aliases['PathRootId'].data_type, Alias)
        self.assertIsInstance(aliases['StructAlias'].data_type, Struct)

        # Ensure struct and union field aliases resolve to proper types
        self.assertIsInstance(data_types['TestStruct'], Struct)

        test_struct = data_types['TestStruct']

        self.assertTrue(len(test_struct.fields), 1)
        field = data_types['TestStruct'].fields[0]
        
        self.assertEqual(field.name, 'field1')
        self.assertIsInstance(field.data_type, Alias)

        test_union = data_types['TestError']

        self.assertTrue(len(test_union.fields), 1)
        field = data_types['TestError'].fields[0]
        
        self.assertEqual(field.name, 'test')
        self.assertIsInstance(field.data_type, Alias)

    def test_no_preserve_aliases_from_api(self):
        spec = """\
namespace preserve_alias

route eval(TestStruct, TestResult, TestError)

alias NamespaceId = String(pattern="[-_0-9a-zA-Z:]+")
alias SharedFolderId = NamespaceId
alias PathRootId = SharedFolderId

struct TestStruct
    field1 PathRootId

alias StructAlias = TestStruct

struct TestResult
    field1 PathRootId

union TestError
    test PathRootId
"""

        api = specs_to_ir(
            [(None, spec)]
        )

        api = remove_aliases_from_api(api)
        
        # Ensure namespace exists
        self.assertEqual(len(api.namespaces), 1)
        self.assertTrue('preserve_alias' in api.namespaces)

        ns = api.namespaces['preserve_alias']

        # Ensure aliases are gone
        self.assertEqual(len(ns.aliases), 0)
    
        data_types = {
            data_type._name: data_type for data_type in ns.data_types
        }

        # Ensure struct and union field aliases resolve to proper types
        self.assertIsInstance(data_types['TestStruct'], Struct)

        test_struct = data_types['TestStruct']

        self.assertTrue(len(test_struct.fields), 1)
        field = data_types['TestStruct'].fields[0]
        
        self.assertEqual(field.name, 'field1')
        self.assertIsInstance(field.data_type, String)

        test_union = data_types['TestError']

        self.assertTrue(len(test_union.fields), 1)
        field = data_types['TestError'].fields[0]
        
        self.assertEqual(field.name, 'test')
        self.assertIsInstance(field.data_type, String)

if __name__ == '__main__':
    unittest.main()
