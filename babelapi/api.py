from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from distutils.version import StrictVersion
import six

from babelapi.data_type import (
    CompositeType,
    ForeignRef,
    doc_unwrap,
    is_composite_type,
    is_list_type,
)

class Api(object):
    """
    A full description of an API's namespaces, data types, and routes.
    """
    def __init__(self, version):
        self.version = StrictVersion(version)
        self.namespaces = OrderedDict()

    def ensure_namespace(self, name):
        """
        Only creates a namespace if it hasn't yet been defined.

        :param str name: Name of the namespace.

        :return ApiNamespace:
        """
        if name not in self.namespaces:
            self.namespaces[name] = ApiNamespace(name)
        return self.namespaces.get(name)

class ApiNamespace(object):
    """
    Represents a category of API endpoints and their associated data types.
    """

    def __init__(self, name):
        self.name = name
        self.doc = None
        self.routes = []
        self.route_by_name = {}
        self.data_types = []
        self.data_type_by_name = {}
        self.referenced_namespaces = []

    def add_doc(self, docstring):
        """Adds a docstring for this namespace.

        The input docstring is normalized to have no leading whitespace and
        no trailing whitespace except for a newline at the end.

        If a docstring already exists, the new normalized docstring is appended
        to the end of the existing one with two newlines separating them.
        """
        assert isinstance(docstring, six.text_type), type(docstring)
        normalized_docstring = docstring.strip() + '\n'
        if self.doc is None:
            self.doc = normalized_docstring
        else:
            self.doc = '%s\n%s' % (self.doc, normalized_docstring)

    def add_route(self, route):
        self.routes.append(route)
        self.route_by_name[route.name] = route

    def add_data_type(self, data_type):
        self.data_types.append(data_type)
        self.data_type_by_name[data_type.name] = data_type

    def add_referenced_namespace(self, namespace):
        """
        For a namespace to be considered "referenced," it must be imported by
        this namespace. Also, at least one data type from the namespace must be
        referenced by this one. The caller of this method is responsible for
        verifying these requirements.
        """
        assert self.name != namespace.name, \
            'Namespace cannot reference itself.'
        if namespace.name not in self.referenced_namespaces:
            self.referenced_namespaces.append(namespace)
            self.referenced_namespaces.sort(key=lambda n: n.name)

    def linearize_data_types(self):
        """
        Returns a list of all data types used in the namespace. Because the
        inheritance of data types can be modeled as a DAG, the list will be a
        linearization of the DAG. It's ideal to generate data types in this
        order so that composite types that reference other composite types are
        defined in the correct order.
        """
        linearized_data_types = []
        seen_data_types = set()

        def add_data_type(data_type):
            if data_type in seen_data_types:
                return
            elif isinstance(data_type, ForeignRef):
                # We're only concerned with types defined in this namespace.
                return
            if isinstance(data_type, CompositeType) and data_type.parent_type:
                add_data_type(data_type.parent_type)
            linearized_data_types.append(data_type)
            seen_data_types.add(data_type)

        for data_type in self.data_types:
            add_data_type(data_type)

        return linearized_data_types

    def distinct_route_io_data_types(self):
        """
        Returns all user-defined data types that are referenced as the request,
        response, or error data type for a route in this namespace.

        The List data type is never returned because it isn't user-defined, but
        if it contains a user-defined type, then that type is included in the
        return set.
        """
        data_types = set()
        for route in self.routes:
            for dtype in (route.request_data_type, route.response_data_type,
                          route.error_data_type):
                while is_list_type(dtype):
                    dtype = dtype.data_type
                if not is_composite_type(dtype):
                    continue
                data_types.add(dtype)
        return data_types

class ApiRoute(object):
    """
    Represents an API endpoint.
    """

    def __init__(self,
                 name,
                 token):
        """
        :param str name: Designated name of the endpoint.
        :param token: Raw route definition from the parser.
        :type token: babelapi.babel.parser.BabelRouteDef
        """
        self.name = name
        self._token = token

    def set_attributes(self, doc, request_data_type, response_data_type,
                       error_data_type, attrs):
        """
        Converts a forward reference definition of a route into a full
        definition.

        :param str doc: Description of the endpoint.
        :type request_data_type: :class:`babelapi.data_type.DataType`
        :type response_data_type: :class:`babelapi.data_type.DataType`
        :type error_data_type: :class:`babelapi.data_type.DataType`
        :param dict attrs: Map of string keys to values that are either int,
            float, bool, str, or None. These are the route attributes assigned
            in the spec.
        """
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)
        self.request_data_type = request_data_type
        self.response_data_type = response_data_type
        self.error_data_type = error_data_type
        self.attrs = attrs
