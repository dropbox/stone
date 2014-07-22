import unittest

from babelsdk.babel.parser import (
    BabelNamespace,
    BabelAlias,
    BabelField,
    BabelParser,
    BabelSymbol,
    BabelTypeDef,
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
        self.assertEqual(out[1].data_type_name, 'String')

    def test_struct_decl(self):

        # test struct decl with no docs
        text = """
namespace files

struct QuotaInfo:
    quota UInt64
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].data_type_name, 'UInt64')

        # test struct with only a top-level doc
        text = """
namespace files

struct QuotaInfo:
    doc::
        The space quota info for a user.
    quota UInt64
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].data_type_name, 'UInt64')

        # test struct with field doc
        text = """
namespace files

struct QuotaInfo:
    doc::
        The space quota info for a user.
    quota UInt64::
        The user's total quota allocation (bytes).
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].data_type_name, 'UInt64')
        self.assertEqual(out[1].fields[0].doc, "The user's total quota allocation (bytes).")

        # test without newline after field doc
        text = """
namespace files

struct QuotaInfo:
    doc::
        The space quota info for a user.
    quota UInt64::
        The user's total quota allocation (bytes)."""

        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertEqual(out[1].doc, 'The space quota info for a user.')
        self.assertEqual(out[1].fields[0].name, 'quota')
        self.assertEqual(out[1].fields[0].data_type_name, 'UInt64')
        self.assertEqual(out[1].fields[0].doc, "The user's total quota allocation (bytes).")

        # test with example
        text = """
namespace files

struct QuotaInfo:
    doc::
        The space quota info for a user.
    quota UInt64::
        The user's total quota allocation (bytes).
    example default:
        quota=64000
"""

        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertIn('default', out[1].examples)

        # test with multiple examples
        text = """
namespace files

struct QuotaInfo:
    doc::
        The space quota info for a user.
    quota UInt64::
        The user's total quota allocation (bytes).
    example default:
        quota=2000000000
    example pro:
        quota=100000000000
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'QuotaInfo')
        self.assertIn('default', out[1].examples)
        self.assertIn('pro', out[1].examples)

    def test_union_decl(self):
        # test union with only symbols
        text = """
namespace files

union Role:
    doc::
        The role a user may have in a shared folder.

    owner::
        Owner of a file.
    viewer::
        Read only permission.
    editor::
        Read and write permission.
"""
        out = self.parser.parse(text)
        self.assertEqual(out[1].name, 'Role')
        self.assertEqual(out[1].doc, 'The role a user may have in a shared folder.')
        self.assertIsInstance(out[1].fields[0], BabelSymbol)
        self.assertEqual(out[1].fields[0].name, 'owner')
        self.assertIsInstance(out[1].fields[1], BabelSymbol)
        self.assertEqual(out[1].fields[1].name, 'viewer')
        self.assertIsInstance(out[1].fields[2], BabelSymbol)
        self.assertEqual(out[1].fields[2].name, 'editor')

        # TODO: Test a union that includes a struct.
