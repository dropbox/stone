import textwrap

from stone.backends.python_client import PythonClientBackend
from stone.ir import (
    ApiNamespace,
    ApiRoute,
    Int32,
    List,
    Map,
    Nullable,
    String,
    Void,
    StructField,
    Struct,
)

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

import unittest

class TestGeneratedPythonClient(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _evaluate_namespace(self, ns):
        # type: (ApiNamespace) -> typing.Text

        backend = PythonClientBackend(
            target_folder_path='output',
            args=['-a', 'scope', '-a', 'another_attribute',
                  '-m', 'files', '-c', 'DropboxBase', '-t', 'dropbox'])
        backend._generate_routes(ns)
        return backend.output_buffer_to_string()

    def _evaluate_namespace_with_auth_mode(self, ns, auth_mode):
        # type: (ApiNamespace, str) -> typing.Text

        # supply supported auth modes to the SDK generator using the new syntax
        backend = PythonClientBackend(
            target_folder_path='output',
            args=['-w', auth_mode, '-m', 'files', '-c', 'DropboxBase', '-t', 'dropbox'])
        backend._generate_route_methods({ns})
        return backend.output_buffer_to_string()

    def test_route_with_version_number(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, ':route:`get_metadata:2`', Void(), Void(), Void(), {})
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace(ns)

        expected = textwrap.dedent('''\
            def files_get_metadata(self):
                """
                :meth:`files_get_metadata_v2`

                :rtype: None
                """
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None

            def files_get_metadata_v2(self):
                arg = None
                r = self.request(
                    files.get_metadata_v2,
                    'files',
                    arg,
                    None,
                )
                return r

        ''')

        self.assertEqual(result, expected)

    def test_route_with_auth_mode1(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, ':route:`get_metadata:2`', Void(), Void(), Void(),
                              {'auth': 'app'})
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(),
                              {'auth': 'user, app'})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace_with_auth_mode(ns, 'user')

        expected = textwrap.dedent('''\
            # ------------------------------------------
            # Routes in files namespace

            def files_get_metadata_v2(self):
                arg = None
                r = self.request(
                    files.get_metadata_v2,
                    'files',
                    arg,
                    None,
                )
                return r

        ''')

        self.assertEqual(result, expected)

    def test_route_with_auth_mode2(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, ':route:`get_metadata:2`', Void(), Void(), Void(),
                              {'auth': 'user'})
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(),
                              {'auth': 'user, app'})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace_with_auth_mode(ns, 'user')

        expected = textwrap.dedent('''\
            # ------------------------------------------
            # Routes in files namespace

            def files_get_metadata(self):
                """
                :meth:`files_get_metadata_v2`

                :rtype: None
                """
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None

            def files_get_metadata_v2(self):
                arg = None
                r = self.request(
                    files.get_metadata_v2,
                    'files',
                    arg,
                    None,
                )
                return r

        ''')

        self.assertEqual(result, expected)

    def test_route_with_auth_mode3(self):
        # type: () -> None

        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, ':route:`get_metadata:2`', Void(), Void(), Void(),
                             {'auth': 'app'})
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(),
                             {'auth': 'app, team'})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace_with_auth_mode(ns, 'user')

        expected = textwrap.dedent('''\
            # ------------------------------------------
            # Routes in files namespace

        ''')

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

    def test_route_argument_doc_string(self):
        backend = PythonClientBackend(
            target_folder_path='output',
            args=['-m', 'files', '-c', 'DropboxBase', '-t', 'dropbox'])
        ns = ApiNamespace('files')
        self.assertEqual(backend._format_type_in_doc(ns, Int32()), 'int')
        self.assertEqual(backend._format_type_in_doc(ns, Void()), 'None')
        self.assertEqual(backend._format_type_in_doc(ns, List(String())), 'List[str]')
        self.assertEqual(backend._format_type_in_doc(ns, Nullable(String())),
                         'Nullable[str]')
        self.assertEqual(backend._format_type_in_doc(ns, Map(String(), Int32())),
                         'Map[str, int]')

    def test_route_with_attributes_in_docstring(self):
        # type: () -> None

        route = ApiRoute('get_metadata', 1, None)
        route.set_attributes(None, None, Void(), Void(), Void(), {
            'scope': 'events.read', 'another_attribute': 'foo'
        })
        ns = ApiNamespace('files')
        ns.add_route(route)

        result = self._evaluate_namespace(ns)
        expected = textwrap.dedent('''\
            def files_get_metadata(self):
                """
                Route attributes:
                    scope: events.read
                    another_attribute: foo

                :rtype: None
                """
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None

        ''')
        self.assertEqual(result, expected)

    def test_route_with_none_attribute_in_docstring(self):
        # type: () -> None

        route = ApiRoute('get_metadata', 1, None)
        route.set_attributes(None, None, Void(), Void(), Void(), {
            'scope': 'events.read', 'another_attribute': None
        })
        ns = ApiNamespace('files')
        ns.add_route(route)

        result = self._evaluate_namespace(ns)
        expected = textwrap.dedent('''\
            def files_get_metadata(self):
                """
                Route attributes:
                    scope: events.read

                :rtype: None
                """
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None

        ''')
        self.assertEqual(result, expected)

    def test_route_with_attributes_and_doc_in_docstring(self):
        # type: () -> None
        """
        In particular make sure there's spacing b/w overview and attrs.
        """

        route = ApiRoute('get_metadata', 1, None)
        route.set_attributes(None, "Test string.", Void(), Void(), Void(),
                             {'scope': 'events.read'})
        ns = ApiNamespace('files')
        ns.add_route(route)

        result = self._evaluate_namespace(ns)
        expected = textwrap.dedent('''\
            def files_get_metadata(self):
                """
                Test string.

                Route attributes:
                    scope: events.read

                :rtype: None
                """
                arg = None
                r = self.request(
                    files.get_metadata,
                    'files',
                    arg,
                    None,
                )
                return None

        ''')
        self.assertEqual(result, expected)

    def test_route_with_doc_and_attribute_and_data_types(self):
        # type: () -> None
        ns = ApiNamespace('files')
        struct = Struct('MyStruct', ns, None)
        struct.set_attributes(None, [
            StructField('field1', Int32(), None, None),
            StructField('field2', Int32(), None, None),
        ])

        route = ApiRoute('test/route', 1, None)
        route.set_attributes(
            None, "Test string.", struct, Int32(), Void(), {'scope': 'events.read'}
        )
        ns.add_route(route)

        result = self._evaluate_namespace(ns)
        expected = textwrap.dedent('''\
            def files_test_route(self,
                                 field1,
                                 field2):
                """
                Test string.

                Route attributes:
                    scope: events.read

                :type field1: int
                :type field2: int
                :rtype: int
                """
                arg = files.MyStruct(field1,
                                     field2)
                r = self.request(
                    files.test_route,
                    'files',
                    arg,
                    None,
                )
                return r

        ''')
        self.assertEqual(result, expected)

    # TODO: add more unit tests for client code generation
