import unittest

from babelapi.babel.parser import (
    BabelNamespace,
    BabelAlias,
    BabelParser,
    BabelSymbolField,
    BabelTagRef,
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

    def test_type_parameters(self):
        text = """
namespace test

alias T = String(min_length=3)
alias F = Float64(max_value=3.2e1)
"""
        out = self.parser.parse(text)
        self.assertIsInstance(out[1], BabelAlias)
        self.assertEqual(out[1].name, 'T')
        self.assertEqual(out[1].type_ref.name, 'String')

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

        # test with coverage
        text = """
namespace files

struct Entry of Folder | File
    id String

struct Folder
    children UInt64

struct File
    size UInt64
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].coverage, ['Folder', 'File'])

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
        self.assertIsInstance(out[1].fields[0], BabelSymbolField)
        self.assertEqual(out[1].fields[0].name, 'owner')
        self.assertIsInstance(out[1].fields[1], BabelSymbolField)
        self.assertEqual(out[1].fields[1].name, 'viewer')
        self.assertIsInstance(out[1].fields[2], BabelSymbolField)
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

route GetAccountInfo(Null, Null, Null)
"""
        # Test route definition with no docstring
        self.parser.parse(text)

        text = """
namespace users

struct AccountInfo
    email String

route GetAccountInfo(AccountInfo, Null, Null)
    "Gets the account info for a user"
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'AccountInfo')
        self.assertEqual(out[2].name, 'GetAccountInfo')
        self.assertEqual(out[2].request_type_ref.name, 'AccountInfo')
        self.assertEqual(out[2].response_type_ref.name, 'Null')
        self.assertEqual(out[2].error_type_ref.name, 'Null')

        # Test raw documentation
        text = """
namespace users

route GetAccountInfo(Null, Null, Null)
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
        char, lineno = self.parser.lexer.errors[0]
        self.assertEqual(char, '%')
        self.assertEqual(lineno, 4)
        char, lineno = self.parser.lexer.errors[1]
        self.assertEqual(char, '%')
        self.assertEqual(lineno, 8)
        # Check that despite lexing errors, parser marched on successfully.
        self.assertEqual(out[1].name, 'AccountInfo')

    def test_parsing_errors(self):
        text = """
namespace users

strct AccountInfo
    email String
"""
        self.parser.parse(text)
        ttype, tvalue, lineno = self.parser.errors[0]
        self.assertEqual(ttype, 'ID')
        self.assertEqual(tvalue, 'strct')
        self.assertEqual(lineno, 4)
