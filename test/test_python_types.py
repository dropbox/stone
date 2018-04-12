import textwrap

from stone.backends.python_types import PythonTypesBackend
from stone.ir import ApiNamespace, ApiRoute, Void, Int32, Struct
from test.backend_test_util import _mock_emit

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

import unittest

class TestGeneratedPythonTypes(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGeneratedPythonTypes, self).__init__(*args, **kwargs)

    def _mk_route_schema(self):
        s = Struct('Route', ApiNamespace('stone_cfg'), None)
        s.set_attributes(None, [], None)
        return s

    def _evaluate_namespace(self, ns):
        # type: (ApiNamespace) -> typing.Text

        backend = PythonTypesBackend(
            target_folder_path='output',
            args=['-r', 'dropbox.dropbox.Dropbox.{ns}_{route}'])
        emitted = _mock_emit(backend)
        route_schema = self._mk_route_schema()
        backend._generate_routes(route_schema, ns)
        result = "".join(emitted)
        return result

    def test_route_with_version_number(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, None, Void(), Void(), Void(), {})
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace(ns)

        expected = textwrap.dedent("""\
            get_metadata = bb.Route(
                'get_metadata',
                1,
                False,
                bv.Void(),
                bv.Void(),
                bv.Void(),
                {},
            )
            get_metadata_v2 = bb.Route(
                'get_metadata',
                2,
                False,
                bv.Void(),
                bv.Int32(),
                bv.Void(),
                {},
            )

            ROUTES = {
                'get_metadata': get_metadata,
                'get_metadata:2': get_metadata_v2,
            }

        """)

        self.assertEqual(result, expected)

    def test_route_with_version_number_name_conflict(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 2, None)
        route1.set_attributes(None, None, Void(), Int32(), Void(), {})
        route2 = ApiRoute('get_metadata_v2', 1, None)
        route2.set_attributes(None, None, Void(), Void(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        with self.assertRaises(RuntimeError) as cm:
            self._evaluate_namespace(ns)
        self.assertEqual(
            'There is a name conflict between {!r} and {!r}'.format(route1, route2),
            str(cm.exception))

    # TODO: add more unit tests for client code generation
