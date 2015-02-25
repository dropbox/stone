import unittest

from babelapi.api import (
    ApiNamespace,
    ApiRoute,
)
from babelapi.data_type import (
    List,
    Boolean,
    String,
    Struct,
    StructField,
)

class TestGenerator(unittest.TestCase):
    """
    Tests the interface exposed to Generators.
    """

    def test_api_namespace(self):
        ns = ApiNamespace('files')
        a1 = Struct('A1', None, [StructField('f1', Boolean(), None)])
        a2 = Struct('A2', None, [StructField('f2', Boolean(), None)])
        l = List(a1)
        s = String()
        route = ApiRoute('test/route', None, l, a2, s, None)
        ns.add_route(route)

        # Test that only user-defined types are returned.
        route_io = ns.distinct_route_io_data_types()
        self.assertIn(a1, route_io)
        self.assertIn(a2, route_io)
        self.assertNotIn(l, route_io)
        self.assertNotIn(s, route_io)
