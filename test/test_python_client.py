import textwrap

from stone.backends.python_client import PythonClientBackend
from stone.ir import ApiNamespace, ApiRoute, Void, Int32
from test.backend_test_util import _mock_emit

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

import unittest

class TestGeneratedPythonClient(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGeneratedPythonClient, self).__init__(*args, **kwargs)

    def _evaluate_namespace(self, ns):
        # type: (ApiNamespace) -> typing.Text

        backend = PythonClientBackend(
            target_folder_path='output',
            args=['-m', 'files', '-c', 'DropboxBase', '-t', 'dropbox'])
        emitted = _mock_emit(backend)
        for route in ns.routes:
            backend._generate_route(ns, route)
        result = "".join(emitted)
        return result

    def test_route_with_version_number(self):
        # type: () -> None

        route_v1 = ApiRoute('get_metadata', 1, None)
        route_v1.set_attributes(None, None, Void(), Void(), Void(), {})
        route_v2 = ApiRoute('get_metadata', 2, None)
        route_v2.set_attributes(None, None, Void(), Int32(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route_v1)
        ns.add_route(route_v2)

        result = self._evaluate_namespace(ns)

        expected = textwrap.dedent("""\
            def files_get_metadata(self):
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None
            
            def files_get_metadata_2(self):
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return r

        """)

        self.assertEqual(result, expected)

    # TODO: add more unit tests for client code generation