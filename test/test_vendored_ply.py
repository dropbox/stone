import inspect
import unittest

from stone._vendor.ply import yacc


class TestVendoredPly(unittest.TestCase):

    def test_pickle_table_support_is_removed(self):
        self.assertNotIn('picklefile', inspect.signature(yacc.yacc).parameters)
        self.assertFalse(hasattr(yacc.LRTable, 'read_pickle'))
        self.assertFalse(hasattr(yacc.LRGeneratedTable, 'pickle_table'))

    def test_picklefile_argument_is_rejected(self):
        with self.assertRaises(TypeError):
            yacc.yacc(picklefile='untrusted.pkl')  # pylint: disable=unexpected-keyword-arg


if __name__ == '__main__':
    unittest.main()
