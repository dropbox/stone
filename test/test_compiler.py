#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import unittest
import sys

from stone.backends.python_types import (
    PythonTypesBackend
)
from stone.compiler import (
    Compiler
)
from stone.frontend.frontend import (
    specs_to_ir
)

class PreserveBackend(PythonTypesBackend):
    preserve_aliases = True

class NoPreserveBackend(PythonTypesBackend):
    preserve_aliases = False

test_preserve_alias_spec = """\
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

test_no_preserve_alias_spec = """\
namespace no_preserve_alias

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

class TestCompiler(unittest.TestCase):

    def test_preserve_aliases_true(self):
        # Use a modified version of the Python types backend
        api = specs_to_ir(
            [(None, test_preserve_alias_spec)]
        )
        backend = PreserveBackend(
            target_folder_path='preserve_output',
            args=['-r', 'dropbox.dropbox.Dropbox.{ns}_{route}']
        )

        compiler = Compiler(
            api,
            backend,
            [],
            "preserve_output",
            clean_build=True
        )
        compiler.build()

        # Ensure module was built
        self.assertTrue(os.path.exists('preserve_output/preserve_alias.py'))

        sys.path.append('preserve_output')

        ns = __import__('preserve_alias')

        # Aliases should exist on the namespace
        self.assertTrue(hasattr(ns, 'NamespaceId_validator'))
        self.assertTrue(hasattr(ns, 'SharedFolderId_validator'))
        self.assertTrue(hasattr(ns, 'PathRootId_validator'))
        self.assertTrue(hasattr(ns, 'StructAlias_validator'))

        # Above Aliases should point to a String
        self.assertIsInstance(ns.NamespaceId_validator, ns.bv.String)
        self.assertIsInstance(ns.SharedFolderId_validator, ns.bv.String)
        self.assertIsInstance(ns.PathRootId_validator, ns.bv.String)
        # StructAlias should point to TestStruct
        self.assertEquals(ns.StructAlias, ns.TestStruct)

        # Alias for struct field should exist and point to PathRootId alias (String)
        self.assertTrue(hasattr(ns.TestStruct, 'field1'))
        self.assertEquals(ns.TestStruct._field1_validator, ns.PathRootId_validator)

        # Alias for union tag should exist and point to PathRootId alias (String)
        self.assertTrue(hasattr(ns.TestError, 'test'))
        self.assertEquals(ns.TestError._tagmap['test'], ns.PathRootId_validator)

    def test_preserve_aliases_false(self):
        # Use a modified version of the Python types backend
        api = specs_to_ir(
            [(None, test_no_preserve_alias_spec)]
        )
        backend = NoPreserveBackend(
            target_folder_path='no_preserve_output',
            args=['-r', 'dropbox.dropbox.Dropbox.{ns}_{route}']
        )

        compiler = Compiler(
            api,
            backend,
            [],
            "no_preserve_output",
            clean_build=True
        )
        compiler.build()

        # Ensure module was built
        self.assertTrue(os.path.exists('no_preserve_output/no_preserve_alias.py'))

        sys.path.append('no_preserve_output')

        ns = __import__('no_preserve_alias')

        # Aliases should NOT exist on the namespace
        self.assertFalse(hasattr(ns, 'NamespaceId_validator'))
        self.assertFalse(hasattr(ns, 'SharedFolderId_validator'))
        self.assertFalse(hasattr(ns, 'PathRootId_validator'))
        self.assertFalse(hasattr(ns, 'StructAlias_validator'))

        # Struct field should exist and point to a String
        self.assertTrue(hasattr(ns.TestStruct, 'field1'))
        self.assertIsInstance(ns.TestStruct._field1_validator, ns.bv.String)

        # Union field should exist and point to a String
        self.assertTrue(hasattr(ns.TestError, 'test'))
        self.assertIsInstance(ns.TestError._tagmap['test'], ns.bv.String)

if __name__ == '__main__':
    unittest.main()
