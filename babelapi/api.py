from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from distutils.version import StrictVersion
import six

from babelapi.data_type import (
    doc_unwrap,
    is_composite_type,
    is_list_type,
    is_nullable_type,
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
        self._imported_namespaces = []

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

    def add_imported_namespace(self, namespace):
        """
        For a namespace to be considered imported, it must be imported by
        this namespace, and have at least one data type from the namespace
        referenced by this one. The caller of this method is responsible for
        verifying these requirements.
        """
        assert self.name != namespace.name, \
            'Namespace cannot import itself.'
        if namespace not in self._imported_namespaces:
            self._imported_namespaces.append(namespace)
            self._imported_namespaces.sort(key=lambda n: n.name)

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
            elif data_type.namespace != self:
                # We're only concerned with types defined in this namespace.
                return
            if is_composite_type(data_type) and data_type.parent_type:
                add_data_type(data_type.parent_type)
            linearized_data_types.append(data_type)
            seen_data_types.add(data_type)

        for data_type in self.data_types:
            add_data_type(data_type)

        return linearized_data_types

    def get_route_io_data_types(self):
        """
        Returns a list of all user-defined data types that are referenced as
        either an argument, result, or error of a route. If a List or Nullable
        data type is referenced, then the contained data type is returned
        assuming it's a user-defined type.
        """
        data_types = set()
        for route in self.routes:
            for dtype in (route.request_data_type, route.response_data_type,
                          route.error_data_type):
                while is_list_type(dtype) or is_nullable_type(dtype):
                    dtype = dtype.data_type
                if is_composite_type(dtype):
                    data_types.add(dtype)

        return sorted(data_types, key=lambda dt: dt.name)

    def get_imported_namespaces(self):
        """
        Returns a list of Namespace objects. A namespace is a member of this
        list if it is imported by the current namespace and a data type is
        referenced from it. Namespaces are in ASCII order by name.
        """
        return self._imported_namespaces[:]

    def get_namespaces_imported_by_route_io(self):
        """
        Returns a list of Namespace objects. A namespace is a member of this
        list if it is imported by the current namespace and has a data type
        from it referenced as an argument, result, or error of a route.
        Namespaces are in ASCII order by name.
        """
        namespace_data_types = sorted(self.get_route_io_data_types(),
                                      key=lambda dt: dt.name)
        referenced_namespaces = set()
        for data_type in namespace_data_types:
            if data_type.namespace != self:
                referenced_namespaces.add(data_type.namespace)
        return sorted(referenced_namespaces, key=lambda n: n.name)

    def __repr__(self):
        return 'ApiNamespace({!r})'.format(self.name)

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

    def __repr__(self):
        return 'ApiRoute({!r})'.format(self.name)
