import unittest

from stone.ir import (
    resolve_aliases,
    Alias,
    String
)

class TestDataTypes(unittest.TestCase):
    """Tests for the data_types module"""

    def test_resolve_aliases(self):
        
        data_type = String()
        resolved = resolve_aliases(data_type)

        # Test that non alias returns itself
        self.assertIsInstance(resolved, String)

        first_alias = Alias(None, None, None)
        first_alias.data_type = String()
        resolved = resolve_aliases(data_type)

        # Test that single-level alias chain resolves
        self.assertIsInstance(resolved, String)
        self.assertIsInstance(first_alias.data_type, String)

        first_alias = Alias(None, None, None)
        second_alias = Alias(None, None, None)
        first_alias.data_type = second_alias
        second_alias.data_type = String()
        resolved = resolve_aliases(data_type)

        # Test that a two-level alias chain resolves
        resolved = resolve_aliases(first_alias)
        self.assertIsInstance(resolved, String)
        self.assertIsInstance(first_alias.data_type, String)
        self.assertIsInstance(second_alias.data_type, String)

