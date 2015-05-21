from __future__ import absolute_import, division, print_function, unicode_literals

import textwrap
import unittest

from babelapi.babel.parser import (
    BabelNamespace,
    BabelAlias,
    BabelParser,
    BabelVoidField,
    BabelTagRef,
)
from babelapi.babel.tower import (
    InvalidSpec,
    TowerOfBabel,
)

class TestBabel(unittest.TestCase):
    """
    Tests the Babel format.
    """

    def setUp(self):
        self.parser = BabelParser(debug=False)

    def test_namespace_decl(self):
        text = """namespace files"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[0], BabelNamespace)
        self.assertEqual(out[0].name, 'files')

        # test starting with newlines
        text = """\n\nnamespace files"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[0], BabelNamespace)
        self.assertEqual(out[0].name, 'files')

    def test_comments(self):
        text = """
# comment at top
namespace files

# another full line comment
alias Rev = String # partial line comment

struct S # comment before INDENT
    "Doc"
    # inner comment
    f1 UInt64 # partial line comment
    # trailing comment

struct S2 # struct def following comment
    # start with comment
    f1 String # end with partial-line comment

# footer comment
"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[0], BabelNamespace)
        self.assertIsInstance(out[1], BabelAlias)
        self.assertEqual(out[2].name, 'S')
        self.assertEqual(out[3].name, 'S2')

    def test_type_args(self):
        text = """
namespace test

alias T = String(min_length=3)
alias F = Float64(max_value=3.2e1)
alias Numbers = List(UInt64)
"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[1], BabelAlias)
        self.assertEqual(out[1].name, 'T')
        self.assertEqual(out[1].type_ref.name, 'String')
        self.assertEqual(out[1].type_ref.args[1]['min_length'], 3)

        self.assertIsInstance(out[2], BabelAlias)
        self.assertEqual(out[2].name, 'F')
        self.assertEqual(out[2].type_ref.name, 'Float64')
        self.assertEqual(out[2].type_ref.args[1]['max_value'], 3.2e1)

        self.assertIsInstance(out[3], BabelAlias)
        self.assertEqual(out[3].name, 'Numbers')
        self.assertEqual(out[3].type_ref.name, 'List')
        self.assertEqual(out[3].type_ref.args[0][0].name, 'UInt64')

    def test_struct_decl(self):

        # test struct decl with no docs
        text = """
namespace files

struct QuotaInfo
    quota UInt64
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].type_ref.name, 'UInt64')

        # test struct with only a top-level doc
        text = """
namespace files

struct QuotaInfo
    "The space quota info for a user."
    quota UInt64
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].type_ref.name, 'UInt64')

        # test struct with field doc
        text = """
namespace files

struct QuotaInfo
    "The space quota info for a user."
    quota UInt64
        "The user's total quota allocation (bytes)."
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].type_ref.name, 'UInt64')
        self.assertEqual(out[1].fields[0].doc, "The user's total quota allocation (bytes).")

        # test without newline after field doc
        text = """
namespace files

struct QuotaInfo
    "The space quota info for a user."
    quota UInt64
        "The user's total quota allocation (bytes)."
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].type_ref.name, 'UInt64')
        self.assertEqual(out[1].fields[0].doc, "The user's total quota allocation (bytes).")

        # test with example
        text = """
namespace files

struct QuotaInfo
    "The space quota info for a user."
    quota UInt64
        "The user's total quota allocation (bytes)."
    example default
        quota=64000
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertIn('default', out[1].examples)

        # test with multiple examples
        text = """
namespace files

struct QuotaInfo
    "The space quota info for a user."
    quota UInt64
        "The user's total quota allocation (bytes)."
    example default
        quota=2000000000
    example pro
        quota=100000000000
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertIn('default', out[1].examples)
        self.assertIn('pro', out[1].examples)

        # test with inheritance
        text = """
namespace test

struct S1
    f1 UInt64

struct S2 extends S1
    f2 String
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'S1')
        self.assertEqual(out[2].name, 'S2')
        self.assertEqual(out[2].extends.name, 'S1')

        # test with defaults
        text = """
namespace ns
struct S
    n1 Int32 = -5
    n2 Int32 = 5
    f1 Float64 = -1.
    f2 Float64 = -4.2
    f3 Float64 = -5e-3
    f4 Float64 = -5.1e-3
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'S')
        self.assertEqual(out[1].fields[0].name, 'n1')
        self.assertTrue(out[1].fields[0].has_default)
        self.assertEqual(out[1].fields[0].default, -5)
        self.assertEqual(out[1].fields[1].default, 5)
        self.assertEqual(out[1].fields[2].default, -1)
        self.assertEqual(out[1].fields[3].default, -4.2)
        self.assertEqual(out[1].fields[4].default, -5e-3)
        self.assertEqual(out[1].fields[5].default, -5.1e-3)

    def test_union_decl(self):
        # test union with only symbols
        text = """
namespace files

union Role
    "The role a user may have in a shared folder."

    owner
        "Owner of a file."
    viewer
        "Read only permission."
    editor
        "Read and write permission."
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'Role')
        self.assertEqual(out[1].doc, 'The role a user may have in a shared folder.')
        self.assertIsInstance(out[1].fields[0], BabelVoidField)
        self.assertEqual(out[1].fields[0].name, 'owner')
        self.assertIsInstance(out[1].fields[1], BabelVoidField)
        self.assertEqual(out[1].fields[1].name, 'viewer')
        self.assertIsInstance(out[1].fields[2], BabelVoidField)
        self.assertEqual(out[1].fields[2].name, 'editor')

        # TODO: Test a union that includes a struct.

        text = """
namespace files

union Error
    A
        "Variant A"
    B
        "Variant B"
    UNK*
"""
        out = self.parser.parse(text)
        self.assertTrue(out[1].fields[2].catch_all)

        # test with inheritance
        text = """
namespace test

union U1
    t1 UInt64

union U2 extends U1
    t2 String
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'U1')
        self.assertEqual(out[2].name, 'U2')
        self.assertEqual(out[2].extends.name, 'U1')

    def test_composition(self):
        text = """
namespace files

union UploadMode
    add
    overwrite

struct Upload
    path String
    mode UploadMode = add
"""
        out = self.parser.parse(text)
        self.assertEqual(out[2].name, 'Upload')
        self.assertIsInstance(out[2].fields[1].default, BabelTagRef)
        self.assertEqual(out[2].fields[1].default.tag, 'add')

    def test_route_decl(self):

        text = """
namespace users

route GetAccountInfo(Void, Void, Void)
"""
        # Test route definition with no docstring
        self.parser.parse(text)

        text = """
namespace users

struct AccountInfo
    email String

route GetAccountInfo(AccountInfo, Void, Void)
    "Gets the account info for a user"
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'AccountInfo')
        self.assertEqual(out[2].name, 'GetAccountInfo')
        self.assertEqual(out[2].request_type_ref.name, 'AccountInfo')
        self.assertEqual(out[2].response_type_ref.name, 'Void')
        self.assertEqual(out[2].error_type_ref.name, 'Void')

        # Test raw documentation
        text = """
namespace users

route GetAccountInfo(Void, Void, Void)
    "0

    1

    2

    3
    "
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].doc, '0\n\n1\n\n2\n\n3\n')

    def test_lexing_errors(self):
        text = """
namespace users

%

# testing line numbers

%

struct AccountInfo
    email String
"""
        out = self.parser.parse(text)
        msg, lineno = self.parser.lexer.errors[0]
        self.assertEqual(msg, "Illegal character '%'.")
        self.assertEqual(lineno, 4)
        msg, lineno = self.parser.lexer.errors[1]
        self.assertEqual(msg, "Illegal character '%'.")
        self.assertEqual(lineno, 8)
        # Check that despite lexing errors, parser marched on successfully.
        self.assertEqual(out[1].name, 'AccountInfo')

        text = """\
namespace test

struct S
    # Indent below is only 3 spaces
   f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("Indent is not divisible by 4.", cm.exception.msg)

    def test_parsing_errors(self):
        text = """
namespace users

strct AccountInfo
    email String
"""
        self.parser.parse(text)
        msg, lineno, path = self.parser.errors[0]
        self.assertEqual(msg, "Unexpected ID with value 'strct'.")
        self.assertEqual(lineno, 4)

        text = """\
namespace users

route test_route(Blah, Blah, Blah)
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("Symbol 'Blah' is undefined", cm.exception.msg)

    def test_docstrings(self):
        text = """
namespace test

# No docstrings at all
struct E
    f String

struct S
    "Only type doc"
    f String

struct T
    f String
        "Only field doc"

union U
    "Only type doc"
    f String

union V
    f String
        "Only field doc"

# Check for inherited doc
struct W extends T
    g String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        E_dt = t.api.namespaces['test'].data_type_by_name['E']
        self.assertFalse(E_dt.has_documented_type_or_fields())
        self.assertFalse(E_dt.has_documented_fields())

        S_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertTrue(S_dt.has_documented_type_or_fields())
        self.assertFalse(S_dt.has_documented_fields())

        T_dt = t.api.namespaces['test'].data_type_by_name['T']
        self.assertTrue(T_dt.has_documented_type_or_fields())
        self.assertTrue(T_dt.has_documented_fields())

        U_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertTrue(U_dt.has_documented_type_or_fields())
        self.assertFalse(U_dt.has_documented_fields())

        V_dt = t.api.namespaces['test'].data_type_by_name['V']
        self.assertTrue(V_dt.has_documented_type_or_fields())
        self.assertTrue(V_dt.has_documented_fields())

        W_dt = t.api.namespaces['test'].data_type_by_name['W']
        self.assertFalse(W_dt.has_documented_type_or_fields())
        self.assertFalse(W_dt.has_documented_fields())
        self.assertFalse(W_dt.has_documented_type_or_fields(), True)
        self.assertFalse(W_dt.has_documented_fields(), True)

    def test_alias(self):
        # Test aliasing to primitive
        text = """
namespace test

alias R = String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test aliasing to primitive with additional attributes and nullable
        text = """
namespace test

alias R = String(min_length=1)?
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test aliasing to alias
        text = """
namespace test

alias T = String
alias R = T
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test aliasing to alias with attributes already set.
        text = """
namespace test

alias T = String(min_length=1)
alias R = T(min_length=1)
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('Attributes cannot be specified for instantiated type',
                      cm.exception.msg)

        # Test aliasing to composite
        text = """
namespace test

struct S
    f String
alias R = S
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test aliasing to composite with attributes
        text = """
namespace test

struct S
    f String

alias R = S(min_length=1)
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('Attributes cannot be specified for instantiated type',
                      cm.exception.msg)

    def test_struct_semantics(self):
        # Test duplicate fields
        text = """\
namespace test

struct A
    a UInt64
    a String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('already defined', cm.exception.msg)

        # Test duplicate field name -- earlier being in a parent type
        text = """\
namespace test

struct A
    a UInt64

struct B extends A
    b String

struct C extends B
    a String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('already defined in parent', cm.exception.msg)

        # Test extending from wrong type
        text = """\
namespace test

union A
    a

struct B extends A
    b UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('struct can only extend another struct', cm.exception.msg)

    def test_union_semantics(self):
        # Test duplicate fields
        text = """\
namespace test

union A
    a UInt64
    a String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('already defined', cm.exception.msg)

        # Test duplicate field name -- earlier being in a parent type
        text = """\
namespace test

union A
    a UInt64

union B extends A
    b String

union C extends B
    a String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('already defined in parent', cm.exception.msg)

        # Test catch-all in generator
        text = """\
namespace test

union A
    a*
    b
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        A_dt = t.api.namespaces['test'].data_type_by_name['A']
        # Test both ways catch-all is exposed
        self.assertEqual(A_dt.catch_all_field, A_dt.fields[0])
        self.assertTrue(A_dt.fields[0].catch_all)

        # Test two catch-alls
        text = """\
namespace test

union A
    a*
    b*
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('Only one catch-all tag', cm.exception.msg)

        # Test existing catch-all in parent type
        text = """\
namespace test

union A
    a*

union B extends A
    b*
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('already declared a catch-all tag', cm.exception.msg)

        # Test extending from wrong type
        text = """\
namespace test

struct A
    a UInt64

union B extends A
    b UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('union can only extend another union', cm.exception.msg)

    def test_enumerated_subtypes(self):

        # Test correct definition
        text = """\
namespace test

struct Resource
    union
        file File
        folder Folder

struct File extends Resource
    size UInt64

struct Folder extends Resource
    icon String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test reference to non-struct
        text = """\
namespace test

struct Resource
    union
        file String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('must be a struct', cm.exception.msg)

        # Test reference to undefined type
        text = """\
namespace test

struct Resource
    union
        file File
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('Undefined', cm.exception.msg)

        # Test reference to non-subtype
        text = """\
namespace test

struct Resource
    union
        file File

struct File
    size UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('not a subtype of', cm.exception.msg)

        # Test subtype listed more than once
        text = """\
namespace test

struct Resource
    union
        file File
        file2 File

struct File extends Resource
    size UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn('only be specified once', cm.exception.msg)

        # Test missing subtype
        text = """\
namespace test

struct Resource
    union
        file File

struct File extends Resource
    size UInt64

struct Folder extends Resource
    icon String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("missing 'Folder'", cm.exception.msg)

        # Test name conflict with field
        text = """\
namespace test

struct Resource
    union
        file File
    file String

struct File extends Resource
    size UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("already defined on", cm.exception.msg)

        # Test name conflict with field in parent
        text = """\
namespace test

struct A
    union
        b B
    c String

struct B extends A
    union
        c C

struct C extends B
    d String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("already defined in parent", cm.exception.msg)

        # Test name conflict with union field in parent
        text = """\
namespace test

struct A
    union
        b B
    c String

struct B extends A
    union
        b C

struct C extends B
    d String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("already defined in parent", cm.exception.msg)

        # Test non-leaf with no enumerated subtypes
        text = """\
namespace test

struct A
    union
        b B
    c String

struct B extends A
    "No enumerated subtypes."

struct C extends B
    union
        d D

struct D extends C
    e String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("cannot enumerate subtypes if parent", cm.exception.msg)

        # Test if a leaf and its parent do not enumerate subtypes, but its
        # grandparent does.
        text = """\
namespace test

struct A
    union
        b B
    c String

struct B extends A
    "No enumerated subtypes."

struct C extends B
    "No enumerated subtypes."
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn("cannot be extended", cm.exception.msg)

    def test_nullable(self):
        # Test stacking nullable
        text = """\
namespace test

alias A = String?
alias B = A?
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Cannot mark reference to nullable type as nullable.',
            cm.exception.msg)

        # Test stacking nullable
        text = """\
namespace test

alias A = String?

struct S
    f A?
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Cannot mark reference to nullable type as nullable.',
            cm.exception.msg)

        # Test extending nullable
        text = """\
namespace test

struct S
    f String

struct T extends S?
    g String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Reference cannot be nullable.',
            cm.exception.msg)

    def test_forward_reference(self):
        # Test route def before struct def
        text = """\
namespace test

route test_route(Void, S, Void)

struct S
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test extending after...
        text = """\
namespace test

struct T extends S
    g String

struct S
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test field ref to later-defined struct
        text = """\
namespace test

route test_route(Void, T, Void)

struct T
    s S

struct S
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test self-reference
        text = """\
namespace test

struct S
    s S?
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

    def test_import(self):
        # Test field reference to another namespace
        ns1_text = """\
namespace ns1

import ns2

struct S
    f ns2.S
"""
        ns2_text = """\
namespace ns2

struct S
    f String
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        t.parse()

        # Test incorrectly importing the current namespace
        text = """\
namespace test
import test
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Cannot import current namespace.',
            cm.exception.msg)

        # Test importing a non-existent namespace
        text = """\
namespace test
import missingns
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Namespace 'missingns' is not defined in any spec.",
            cm.exception.msg)

        # Test extending struct from another namespace
        ns1_text = """\
namespace ns1

import ns2

struct S extends ns2.T
    f String
"""
        ns2_text = """\
namespace ns2

struct T
    g String
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        t.parse()

        # Test extending struct from another namespace that is marked nullable
        ns1_text = """\
namespace ns1

import ns2

struct S extends ns2.X
    f String
"""
        ns2_text = """\
namespace ns2

alias X = T?

struct T
    g String
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'A struct cannot extend a nullable type.',
            cm.exception.msg)

        # Test extending union from another namespace
        ns1_text = """\
namespace ns1

import ns2

union V extends ns2.U
    b String
"""
        ns2_text = """\
namespace ns2

union U
    a
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        t.parse()

        # Test structs that reference one another
        ns1_text = """\
namespace ns1

import ns2

struct S
    t ns2.T
"""
        ns2_text = """\
namespace ns2

import ns1

struct T
    s ns1.S
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        t.parse()

        # Test mutual inheritance, which can't possibly work.
        ns1_text = """\
namespace ns1

import ns2

struct S extends ns2.T
    a String
"""
        ns2_text = """\
namespace ns2

import ns1

struct T extends ns1.S
    b String
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertIn(
            'Unresolvable circular reference',
            cm.exception.msg)

    def test_doc_refs(self):
        # Test union doc referencing field
        text = """\
namespace test

union U
    ":field:`a`"
    a
    b
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        # Test union field doc referencing other field
        text = """\
namespace test

union U
    a
        ":field:`b`"
    b
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

    def test_namespace(self):
        # Test that namespace docstrings are combined
        ns1_text = """\
namespace ns1
    "
    This is a docstring for ns1.
    "

struct S
    f String
"""
        ns2_text = """\
namespace ns1
    "
    This is another docstring for ns1.
    "

struct S2
    f String
"""
        t = TowerOfBabel([('ns1.babel', ns1_text), ('ns2.babel', ns2_text)])
        t.parse()
        self.assertEqual(
            t.api.namespaces['ns1'].doc,
            'This is a docstring for ns1.\n\nThis is another docstring for ns1.\n')

    def test_examples(self):

        # Test simple struct example
        text = """\
namespace test

struct S
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_types[0]
        self.assertTrue(s_dt.get_examples()['default'], {'f': 'A'})

        # Test example with bad type
        text = """\
namespace test

struct S
    f String

    example default
        f = 5
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Bad example for field 'f': integer is not a valid string",
            cm.exception.msg)

        # Test example with label "true". "false" and "null" are also
        # disallowed because they conflict with the identifiers for primitives.
        text = """\
namespace test

struct S
    f String

    example true
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            # This raises an unexpected token error.
            t.parse()

        # Test error case where two examples share the same label
        text = """\
namespace test

struct S
    f String

    example default
        f = "ZZZZZZ3"
    example default
        f = "ZZZZZZ4"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Example with label 'default' already defined on line 6.",
            cm.exception.msg)

        # Test error case where an example has the same field defined twice.
        text = """\
namespace test

struct S
    f String

    example default
        f = "ZZZZZZ3"
        f = "ZZZZZZ4"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Example with label 'default' defines field 'f' more than once.",
            cm.exception.msg)

        # Test empty examples
        text = """\
namespace test

struct S

    example default
    example other
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_types[0]
        self.assertIn('default', s_dt.get_examples())
        self.assertIn('other', s_dt.get_examples())
        self.assertNotIn('missing', s_dt.get_examples())

        # Test missing field in example
        text = """\
namespace test

struct S
    f String

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Missing field 'f' in example.",
            cm.exception.msg)

        # Test missing default example
        text = """\
namespace test

struct S
    t T

    example default

struct T
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Missing field 't' in example.",
            cm.exception.msg)

        # Test primitive field with default will use the default in the
        # example if it's missing.
        text = """\
namespace test

struct S
    f String = "S"

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_types[0]
        # Example should have no keys
        self.assertEqual(s_dt.get_examples()['default'].value['f'], 'S')

        # Test nullable primitive field missing from example
        text = """\
namespace test

struct S
    f String?

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_types[0]
        # Example should have no keys
        self.assertEqual(len(s_dt.get_examples()['default'].value), 0)

        # Test nullable primitive field explicitly set to null in example
        text = """\
namespace test

struct S
    f String?

    example default
        f = null
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_types[0]
        # Example should have no keys
        self.assertEqual(len(s_dt.get_examples()['default'].value), 0)

        # Test non-nullable primitive field explicitly set to null in example
        text = """\
namespace test

struct S
    f String

    example default
        f = null
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Bad example for field 'f': null is not a valid string",
            cm.exception.msg)

        # TODO(kelkabany): Example of lists of primitives doesn't work because
        # the parser doesn't support declaring a list.
        # TODO(kelkabany): Need a way to specify an example of a list of
        # composites where more than one entry comes back.

        # Test field of list of primitives with bad example
        text = """\
namespace test

struct S
    l List(String)

    example default
        l = "a"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Example for field 'l' is unsupported because it's a list of primitives.",
            cm.exception.msg)

        # Test example of list of composite types
        text = """\
namespace test

struct S
    l List(T)

    example default
        l = default

struct T
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'l': [{'f': 'A'}]})

        # Test example of composite type
        text = """\
namespace test

struct S
    t T

    example default
        t = default

struct T
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'t': {'f': 'A'}})

        # Test nullable composite missing from example
        text = """\
namespace test

struct S
    t T?

    example default
        t = default

struct T
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'t': {'f': 'A'}})

        # Test nullable composite explicitly set to null
        text = """\
namespace test

struct S
    t T?

    example default
        t = null

struct T
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {})

        # Test custom label
        text = """\
namespace test

struct S
    t T?

    example default
        t = special

struct T
    f String
    r R

    example default
        f = "A"
        r = default

    example special
        f = "B"
        r = other

struct R
    g String

    example default
        g = "D"

    example other
        g = "C"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'t': {'f': 'B', 'r': {'g': 'C'}}})

        # Test missing label for composite example
        text = """\
namespace test

struct S
    t T?

    example default
        t = missing

struct T
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Reference to example for 'T' with label 'missing' does not exist.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 7)

        # Test missing label for composite example
        text = """\
namespace test

struct S
    t T

    example default

struct T
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Missing field 't' in example.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 6)

        # Test bad label for composite example
        text = """\
namespace test

struct S
    t T?

    example default
        t = 34

struct T
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Field 't' must be set to an example label for type 'T'.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 7)

        # Test with list of composites
        text = """\
namespace test

struct S
    a List(List(T))

    example default
        a = default

struct T
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'a': [[{'f': 'A'}]]})

        # Test with list of primitives
        text = """\
namespace test

struct S
    a List(List(String))

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'a': [[]]})

        # Test solution for recursive struct
        # TODO: Omitting `s=null` will result in infinite recursion.
        text = """\
namespace test

struct S
    s S?
    f String

    example default
        f = "A"
        s = null
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value, {'f': 'A'})

        # Test examples with inheritance trees
        text = """\
namespace test

struct A
    a String

struct B extends A
    b String

struct C extends B
    c String

    example default
        a = "A"
        b = "B"
        c = "C"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()

        text = """\
namespace test

struct A
    a String

struct B extends A
    b String

struct C extends B
    c String

    example default
        b = "B"
        c = "C"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Missing field 'a' in example.",
            cm.exception.msg)

    def test_examples_union(self):
        # Test bad example with no fields specified
        text = """\
namespace test

union U
    a

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Example for union must specify exactly one tag.',
            cm.exception.msg)

        # Test bad example with more than one field specified
        text = """\
namespace test

union U
    a String
    b String

    example default
        a = "A"
        b = "B"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            'Example for union must specify exactly one tag.',
            cm.exception.msg)

        # Test bad example with unknown tag
        text = """\
namespace test

union U
    a String

    example default
        z = "Z"
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Unknown tag 'z' in example.",
            cm.exception.msg)

        # Test bad example with reference
        text = """\
namespace test

union U
    a String

    example default
        a = default
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Tag 'a' had bad example: reference is not a valid string",
            cm.exception.msg)

        # Test bad example with null value for non-nullable
        text = """\
namespace test

union U
    a String

    example default
        a = null
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Tag 'a' is not nullable but is set to null by example.",
            cm.exception.msg)

        # Test example with null value for void type member
        text = """\
namespace test

union U
    a

    example default
        a = null
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        u_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertEqual(u_dt.get_examples()['default'].value, 'a')

        # Test simple union
        text = """\
namespace test

union U
    a
    b String
    c UInt64

    example default
        b = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        u_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertEqual(u_dt.get_examples()['default'].value,
                         {'b': 'A'})
        self.assertEqual(u_dt.get_examples()['a'].value, 'a')
        self.assertNotIn('b', u_dt.get_examples())

        # Test union with list
        text = """\
namespace test

union U
    a List(List(S))

    example default
        a = default

struct S
    f String

    example default
        f = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        u_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertEqual(u_dt.get_examples()['default'].value,
                         {'a': [[{'f': 'A'}]]})

        # Test union with list of primitives
        text = """\
namespace test

union U
    a List(List(String))

    example default
        a = "hi"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        u_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertEqual(u_dt.get_examples()['default'].value,
                         {'a': [['hi']]})

        # Test union with list of primitives (bad type)
        text = """\
namespace test

union U
    a List(List(String))

    example default
        a = 42
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Tag 'a' had bad example: integer is not a valid string",
            cm.exception.msg)

        # Test union with inheritance
        text = """\
namespace test

union U
    a String

union V extends U
    b String

    example default
        a = "A"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        v_dt = t.api.namespaces['test'].data_type_by_name['V']
        self.assertEqual(v_dt.get_examples()['default'].value,
                         {'a': 'A'})

        # Test union and struct
        text = """\
namespace test

union U
    a
    s S

    example default
        s = default

    example other
        s = other

struct S
    f String

    example default
        f = "F"

    example other
        f = "O"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        u_dt = t.api.namespaces['test'].data_type_by_name['U']
        self.assertEqual(u_dt.get_examples()['default'].value,
                         {'s': {'f': 'F'}})
        self.assertEqual(u_dt.get_examples()['other'].value,
                         {'s': {'f': 'O'}})

        # Test union referencing non-existent struct example
        text = """\
namespace test

union U
    a
    s S

    example default
        s = missing

struct S
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Reference to example for 'S' with label 'missing' does not exist.",
            cm.exception.msg)

        # Test fallback to union void member
        text = """\
namespace test

struct S
    u U

    example default
        u = a

union U
    a
    b
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'u': 'a'})

        # Test fallback to union member of composite type
        text = """\
namespace test

struct S
    u U

    example default
        u = default

union U
    a
    b S2

    example default
        b = default

struct S2
    f String

    example default
        f = "F"
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'u': {'b': {'f': 'F'}}})

        # Test TagRef
        text = """\
namespace test

union U
    a
    b

struct S
    u U = a

    example default
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        s_dt = t.api.namespaces['test'].data_type_by_name['S']
        self.assertEqual(s_dt.get_examples()['default'].value,
                         {'u': 'a'})

        # Test bad void union member example value
        text = """\
namespace test

union U
    a

    example default
        a = false
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Tag 'a' had bad example: void type can only be null",
            cm.exception.msg)

    def test_examples_enumerated_subtypes(self):
        # Test missing custom example
        text = """\
namespace test

struct S
    t T

    example other

struct T
    f String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Missing field 't' in example.",
            cm.exception.msg)

        # Test with two subtypes referenced
        text = """\
namespace test

struct R
    union
        s S
        t T
    a String

    example default
        s = default
        t = default

struct S extends R
    b String

struct T extends R
    c String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Example for struct with enumerated subtypes must only specify one subtype tag.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 9)

        # Test bad subtype reference
        text = """\
namespace test

struct R
    union
        s S
        t T
    a String

    example default
        s = 34

struct S extends R
    b String

struct T extends R
    c String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Example of struct with enumerated subtypes must be a reference "
            "to a subtype's example.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 10)

        # Test unknown subtype
        text = """\
namespace test

struct R
    union
        s S
        t T
    a String

    example default
        z = default

struct S extends R
    b String

struct T extends R
    c String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Unknown subtype tag 'z' in example.",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 10)

        # Test correct example of enumerated subtypes
        text = """\
namespace test

struct R
    union
        s S
        t T
    a String

    example default
        s = default

struct S extends R
    b String

    example default
        a = "A"
        b = "B"

struct T extends R
    c String
"""
        t = TowerOfBabel([('test.babel', text)])
        t.parse()
        r_dt = t.api.namespaces['test'].data_type_by_name['R']
        self.assertEqual(r_dt.get_examples()['default'].value,
                         {'a': 'A', 's': {'b': 'B'}})

        # Test missing custom example
        text = """\
namespace test

struct R
    union
        s S
        t T
    a String

    example default
        s = default

struct S extends R
    b String

struct T extends R
    c String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Reference to example for 'S' with label 'default' does not exist.",
            cm.exception.msg)

    def test_name_conflicts(self):
        # Test name conflict in same file
        text = """\
namespace test

struct S
    f String

struct S
    g String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Symbol 'S' already defined (test.babel:3).",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 6)

        # Test name conflict by route
        text = """\
namespace test

struct S
    f String

route S (Void, Void, Void)
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Symbol 'S' already defined (test.babel:3).",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 6)

        # Test name conflict by union
        text = """\
namespace test

struct S
    f String

union S
    g String
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Symbol 'S' already defined (test.babel:3).",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 6)

        # Test name conflict by alias
        text = """\
namespace test

struct S
    f String

alias S = UInt64
"""
        t = TowerOfBabel([('test.babel', text)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Symbol 'S' already defined (test.babel:3).",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 6)

        # Test name from two specs that are part of the same namespace
        text1 = """\
namespace test

struct S
    f String
"""
        text2 = """\
namespace test


struct S
    f String
"""
        t = TowerOfBabel([('test1.babel', text1), ('test2.babel', text2)])
        with self.assertRaises(InvalidSpec) as cm:
            t.parse()
        self.assertEqual(
            "Symbol 'S' already defined (test1.babel:3).",
            cm.exception.msg)
        self.assertEqual(cm.exception.lineno, 4)

    def test_referenced_namespaces(self):
        text1 = textwrap.dedent("""\
            namespace ns1
            struct S1
                f1 String
            struct S2
                f2 String
        """)
        text2 = textwrap.dedent("""\
            namespace ns2
            import ns1
            struct S3
                f3 String
            route r1(ns1.S1, ns1.S2, S3)
        """)
        t = TowerOfBabel([('ns1.babel', text1), ('ns2.babel', text2)])
        t.parse()
        self.assertEqual(t.api.namespaces['ns2'].referenced_namespaces,
                         [t.api.namespaces['ns1']])
        xs = t.api.namespaces['ns2'].distinct_route_io_data_types()
        xs = sorted(xs, key=lambda x: x.name.lower())
        self.assertEqual(len(xs), 3)
        self.assertEqual(xs[0].name, 'ns1.S1')
        self.assertEqual(xs[1].name, 'ns1.S2')
        self.assertEqual(xs[2].name, 'S3')
