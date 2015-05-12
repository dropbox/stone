from __future__ import absolute_import, division, print_function, unicode_literals

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

    def test_alias_decl(self):

        # test first line a newline
        text = """
namespace files

# simple comment
alias Rev = String
"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[1], BabelAlias)
        self.assertEqual(out[1].name, 'Rev')
        self.assertEqual(out[1].type_ref.name, 'String')

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
        self.assertEqual(out[2].extends, 'S1')

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
        self.assertEqual(out[2].extends, 'U1')

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
        ttype, tvalue, lineno, msg = self.parser.errors[0]
        self.assertEqual(ttype, 'ID')
        self.assertEqual(tvalue, 'strct')
        self.assertEqual(lineno, 4)

        text = """\
namespace users

route test_route(Blah, Blah, Blah)
"""
        res = self.parser.parse(text)

        t = TowerOfBabel([])

        with self.assertRaises(InvalidSpec) as cm:
            t.add_to_api('test.babel', res)
        self.assertIn("Symbol 'Blah' is undefined", cm.exception.msg)

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
