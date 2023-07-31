import textwrap
import unittest

from stone.backends.tsd_client import TSDClientBackend
from stone.ir import Api, ApiNamespace, ApiRoute, Void, Int32
from stone.ir.data_types import Struct

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression


class TestGeneratedTSDClient(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_api(self):
        # type () -> Api
        api = Api(version='0.1b1')
        api.route_schema = Struct('Route', 'stone_cfg', None)
        route1 = ApiRoute('get_metadata', 1, None)
        route1.set_attributes(None, ':route:`get_metadata`', Void(), Void(), Void(), {
            'scope': 'events.read'
        })
        route2 = ApiRoute('get_metadata', 2, None)
        route2.set_attributes(None, ':route:`get_metadata:2`', Void(), Int32(), Void(), {
            'scope': 'events.read'
        })
        route3 = ApiRoute('get_metadata', 3, None)
        route3.set_attributes(None, ':route:`get_metadata:3`', Int32(), Int32(), Void(), {
            'scope': None
        })
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)
        ns.add_route(route3)
        api.namespaces[ns.name] = ns
        return api, ns

    def test__generate_types_single_ns(self):
        # type: () -> None
        api, _ = self._get_api()
        backend = TSDClientBackend(
            target_folder_path="output",
            args=['files', 'files']
        )
        backend._generate_routes(api, 0, 0)
        result = backend.output_buffer_to_string()
        expected = textwrap.dedent(
            '''\

            /**
             * getMetadata()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadata(): Promise<void>;

            /**
             * getMetadataV2()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadataV2(): Promise<number>;

            /**
             * getMetadataV3()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             * @param arg The request parameters.
             */
            public filesGetMetadataV3(arg: number): Promise<number>;
            ''')
        self.assertEqual(result, expected)

    def test__generate_types_with_wrap_response_flag(self):
        # type: () -> None
        api, _ = self._get_api()
        backend = TSDClientBackend(
            target_folder_path="output",
            args=['files', 'files', '--wrap-response-in', 'DropboxResponse']
        )
        backend._generate_routes(api, 0, 0)
        result = backend.output_buffer_to_string()
        expected = textwrap.dedent(
            '''\

            /**
             * getMetadata()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadata(): Promise<DropboxResponse<void>>;

            /**
             * getMetadataV2()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadataV2(): Promise<DropboxResponse<number>>;

            /**
             * getMetadataV3()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             * @param arg The request parameters.
             */
            public filesGetMetadataV3(arg: number): Promise<DropboxResponse<number>>;
            ''')
        self.assertEqual(result, expected)

    def test_route_with_version_number_conflict(self):
        # type: () -> None
        api, ns = self._get_api()

        # Add a conflicting route
        route3 = ApiRoute('get_metadata_v2', 1, None)
        route3.set_attributes(None, None, Void(), Int32(), Void(), {})
        ns.add_route(route3)

        backend = TSDClientBackend(
            target_folder_path="output",
            args=['files', 'files']
        )
        with self.assertRaises(RuntimeError) as cm:
            backend._generate_routes(api, 0, 0)
        self.assertTrue(str(cm.exception).startswith(
            'There is a name conflict between'))

    def test_route_with_attributes_in_docstring(self):
        # type: () -> None
        api, _ = self._get_api()
        backend = TSDClientBackend(
            target_folder_path="output",
            args=['files', 'files', '-a', 'scope']
        )
        backend._generate_routes(api, 0, 0)
        result = backend.output_buffer_to_string()
        expected = textwrap.dedent(
            '''\

            /**
             * getMetadata()
             *
             * Route attributes:
             *   scope: events.read
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadata(): Promise<void>;

            /**
             * getMetadataV2()
             *
             * Route attributes:
             *   scope: events.read
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             */
            public filesGetMetadataV2(): Promise<number>;

            /**
             * getMetadataV3()
             *
             * When an error occurs, the route rejects the promise with type Error<void>.
             * @param arg The request parameters.
             */
            public filesGetMetadataV3(arg: number): Promise<number>;
            ''')
        self.assertEqual(result, expected)
