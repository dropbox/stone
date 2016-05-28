from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from distutils.version import StrictVersion
import six

from stone.data_type import (
    doc_unwrap,
    is_alias,
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
        self.route_schema = None

    def ensure_namespace(self, name):
        """
        Only creates a namespace if it hasn't yet been defined.

        :param str name: Name of the namespace.

        :return ApiNamespace:
        """
        if name not in self.namespaces:
            self.namespaces[name] = ApiNamespace(name)
        return self.namespaces.get(name)

    def normalize(self):
        """
        Alphabetizes namespaces and routes to make spec parsing order mostly
        irrelevant.
        """
        ordered_namespaces = OrderedDict()
        # self.namespaces is currently ordered by declaration order.
        for namespace_name in sorted(self.namespaces.keys()):
            ordered_namespaces[namespace_name] = self.namespaces[namespace_name]
        self.namespaces = ordered_namespaces

        for namespace in self.namespaces.values():
            namespace.normalize()

    def add_route_schema(self, route_schema):
        assert self.route_schema is None
        self.route_schema = route_schema

class _ImportReason(object):
    """
    Tracks the reason a namespace was imported.
    """

    def __init__(self):
        self.alias = False
        self.data_type = False


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
        self.aliases = []
        self.alias_by_name = {}
        # Dict[Namespace, _ImportReason]
        self._imported_namespaces = {}

    def add_doc(self, docstring):
        """Adds a docstring for this namespace.

        The input docstring is normalized to have no leading whitespace and
        no trailing whitespace except for a newline at the end.

        If a docstring already exists, the new normalized docstring is appended
        to the end of the existing one with two newlines separating them.
        """
        assert isinstance(docstring, six.text_type), type(docstring)
        normalized_docstring = doc_unwrap(docstring) + '\n'
        if self.doc is None:
            self.doc = normalized_docstring
        else:
            self.doc += normalized_docstring

    def add_route(self, route):
        self.routes.append(route)
        self.route_by_name[route.name] = route

    def add_data_type(self, data_type):
        self.data_types.append(data_type)
        self.data_type_by_name[data_type.name] = data_type

    def add_alias(self, alias):
        self.aliases.append(alias)
        self.alias_by_name[alias.name] = alias

    def add_imported_namespace(self,
                               namespace,
                               imported_alias=False,
                               imported_data_type=False):
        """
        Keeps track of namespaces that this namespace imports.

        Args:
            namespace (Namespace): The imported namespace.
            imported_alias (bool): Set if this namespace references an alias
                in the imported namespace.
            imported_data_type (bool): Set if this namespace references a
                data type in the imported namespace.
        """
        assert self.name != namespace.name, \
            'Namespace cannot import itself.'
        reason = self._imported_namespaces.setdefault(namespace, _ImportReason())
        if imported_alias:
            reason.alias = True
        if imported_data_type:
            reason.data_type = True

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

    def linearize_aliases(self):
        """
        Returns a list of all aliases used in the namespace. The aliases are
        ordered to ensure that if they reference other aliases those aliases
        come earlier in the list.
        """
        linearized_aliases = []
        seen_aliases = set()

        def add_alias(alias):
            if alias in seen_aliases:
                return
            elif alias.namespace != self:
                return
            if is_alias(alias.data_type):
                add_alias(alias.data_type)
            linearized_aliases.append(alias)
            seen_aliases.add(alias)

        for alias in self.aliases:
            add_alias(alias)

        return linearized_aliases

    def get_route_io_data_types(self):
        """
        Returns a list of all user-defined data types that are referenced as
        either an argument, result, or error of a route. If a List or Nullable
        data type is referenced, then the contained data type is returned
        assuming it's a user-defined type.
        """
        data_types = set()
        for route in self.routes:
            for dtype in (route.arg_data_type, route.result_data_type,
                          route.error_data_type):
                while is_list_type(dtype) or is_nullable_type(dtype):
                    dtype = dtype.data_type
                if is_composite_type(dtype) or is_alias(dtype):
                    data_types.add(dtype)

        return sorted(data_types, key=lambda dt: dt.name)

    def get_imported_namespaces(self, must_have_imported_data_type=False):
        """
        Returns a list of Namespace objects. A namespace is a member of this
        list if it is imported by the current namespace and a data type is
        referenced from it. Namespaces are in ASCII order by name.

        Args:
            must_have_imported_data_type (bool): If true, return does not
                include namespaces that were imported only for aliases.

        Returns:
            List[Namespace]: A list of imported namespaces.
        """
        imported_namespaces = []
        for imported_namespace, reason in self._imported_namespaces.items():
            if must_have_imported_data_type and not reason.data_type:
                continue
            imported_namespaces.append(imported_namespace)
        imported_namespaces.sort(key=lambda n: n.name)
        return imported_namespaces

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

    def normalize(self):
        """
        Alphabetizes routes to make route declaration order irrelevant.
        """
        self.routes.sort(key=lambda route: route.name)
        self.data_types.sort(key=lambda data_type: data_type.name)
        self.aliases.sort(key=lambda alias: alias.name)

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
        :type token: stone.stone.parser.StoneRouteDef
        """
        self.name = name
        self._token = token

        # These attributes are set later by set_attributes()
        self.deprecated = None
        self.raw_doc = None
        self.doc = None
        self.arg_data_type = None
        self.result_data_type = None
        self.error_data_type = None
        self.attrs = None

    def set_attributes(self, deprecated, doc, arg_data_type, result_data_type,
                       error_data_type, attrs):
        """
        Converts a forward reference definition of a route into a full
        definition.

        :param DeprecationInfo deprecated: Set if this route is deprecated.
        :param str doc: Description of the endpoint.
        :type arg_data_type: :class:`stone.data_type.DataType`
        :type result_data_type: :class:`stone.data_type.DataType`
        :type error_data_type: :class:`stone.data_type.DataType`
        :param dict attrs: Map of string keys to values that are either int,
            float, bool, str, or None. These are the route attributes assigned
            in the spec.
        """
        self.deprecated = deprecated
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)
        self.arg_data_type = arg_data_type
        self.result_data_type = result_data_type
        self.error_data_type = error_data_type
        self.attrs = attrs

    def __repr__(self):
        return 'ApiRoute({!r})'.format(self.name)


class DeprecationInfo(object):

    def __init__(self, by=None):
        """
        :param ApiRoute by: The route that replaces this deprecated one.
        """
        assert by is None or isinstance(by, ApiRoute), repr(by)
        self.by = by
