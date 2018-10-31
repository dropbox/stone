import unittest

from stone.ir import (
    resolve_aliases,
    Alias,
    String
)

class TestDataTypes(unittest.TestCase):
    """Tests for the data_types module"""

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
