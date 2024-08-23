import unittest

from stone.ir import ApiRoute


class TestApiRoute(unittest.TestCase):
    def test_stable_sort(self):
        """
        Tests API Route sorts according to name and then version
        """
        routes = [
            ApiRoute("B", 1, None),
            ApiRoute("A", 2, None),
            ApiRoute("A", 1, None),
            ApiRoute("B", 2, None),
        ]

        expected = [("A", 1), ("A", 2), ("B", 1), ("B", 2)]
        sorted_routes = list(map(lambda x: (x.name, x.version), sorted(routes)))
        self.assertEqual(sorted_routes, expected)

        reversed_sorted_routes = list(map(lambda x: (x.name, x.version), sorted(reversed(routes))))
        self.assertEqual(reversed_sorted_routes, expected)
