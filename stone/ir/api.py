import typing
from collections import OrderedDict
from distutils.version import StrictVersion

from stone.frontend.ast import AstRouteDef

from .data_types import (
    Alias,
    Annotation,
    AnnotationType,
    DataType,
    Struct,
    UserDefined,
    doc_unwrap,
    is_alias,
    is_composite_type,
    is_list_type,
    is_nullable_type,
)

NamespaceDict = typing.Dict[typing.Text, "ApiNamespace"]


class Api:
    """
    A full description of an API's namespaces, data types, and routes.
    """

    def __init__(self, version: str) -> None:
        self.version = StrictVersion(version)
        self.namespaces: NamespaceDict = OrderedDict()
        self.route_schema: typing.Optional[Struct] = None

    def ensure_namespace(self, name: str) -> "ApiNamespace":
        """
        Only creates a namespace if it hasn't yet been defined.

        :param str name: Name of the namespace.

        :return ApiNamespace:
        """
        if name not in self.namespaces:
            self.namespaces[name] = ApiNamespace(name)
        return self.namespaces[name]

    def normalize(self) -> None:
        """
        Alphabetizes namespaces and routes to make spec parsing order mostly
        irrelevant.
        """
        ordered_namespaces: NamespaceDict = OrderedDict()
        # self.namespaces is currently ordered by declaration order.
        for namespace_name in sorted(self.namespaces.keys()):
            ordered_namespaces[namespace_name] = self.namespaces[namespace_name]
        self.namespaces = ordered_namespaces

        for namespace in self.namespaces.values():
            namespace.normalize()

    def add_route_schema(self, route_schema: Struct) -> None:
        assert self.route_schema is None
        self.route_schema = route_schema


class _ImportReason:
    """
    Tracks the reason a namespace was imported.
    """

    def __init__(self) -> None:
        self.alias = False
        self.data_type = False
        self.annotation = False
        self.annotation_type = False


class ApiNamespace:
    """
    Represents a category of API endpoints and their associated data types.
    """

    def __init__(self, name: typing.Text) -> None:
        self.name = name
        self.doc: typing.Optional[str] = None
        self.routes: typing.List["ApiRoute"] = []
        # TODO (peichao): route_by_name is deprecated by routes_by_name and should be removed.
        self.route_by_name: typing.Dict[typing.Text, "ApiRoute"] = {}
        self.routes_by_name: typing.Dict[typing.Text, "ApiRoutesByVersion"] = {}
        self.data_types: typing.List[UserDefined] = []
        self.data_type_by_name: typing.Dict[str, UserDefined] = {}
        self.aliases: typing.List[Alias] = []
        self.alias_by_name: typing.Dict[str, Alias] = {}
        self.annotations: typing.List[Annotation] = []
        self.annotation_by_name: typing.Dict[str, Annotation] = {}
        self.annotation_types: typing.List[AnnotationType] = []
        self.annotation_type_by_name: typing.Dict[str, AnnotationType] = {}
        self._imported_namespaces: typing.Dict[ApiNamespace, _ImportReason] = {}

    def add_doc(self, docstring: str) -> None:
        """Adds a docstring for this namespace.

        The input docstring is normalized to have no leading whitespace and
        no trailing whitespace except for a newline at the end.

        If a docstring already exists, the new normalized docstring is appended
        to the end of the existing one with two newlines separating them.
        """
        assert isinstance(docstring, str), type(docstring)
        normalized_docstring = doc_unwrap(docstring) + "\n"
        if self.doc is None:
            self.doc = normalized_docstring
        else:
            self.doc += normalized_docstring

    def add_route(self, route: "ApiRoute") -> None:
        self.routes.append(route)
        if route.version == 1:
            self.route_by_name[route.name] = route
        if route.name not in self.routes_by_name:
            self.routes_by_name[route.name] = ApiRoutesByVersion()
        self.routes_by_name[route.name].at_version[route.version] = route

    def add_data_type(self, data_type: UserDefined) -> None:
        self.data_types.append(data_type)
        self.data_type_by_name[data_type.name] = data_type

    def add_alias(self, alias: Alias) -> None:
        self.aliases.append(alias)
        self.alias_by_name[alias.name] = alias

    def add_annotation(self, annotation: Annotation) -> None:
        self.annotations.append(annotation)
        self.annotation_by_name[annotation.name] = annotation

    def add_annotation_type(self, annotation_type: AnnotationType) -> None:
        self.annotation_types.append(annotation_type)
        self.annotation_type_by_name[annotation_type.name] = annotation_type

    def add_imported_namespace(
        self,
        namespace: "ApiNamespace",
        imported_alias: bool = False,
        imported_data_type: bool = False,
        imported_annotation: bool = False,
        imported_annotation_type: bool = False,
    ) -> None:
        """
        Keeps track of namespaces that this namespace imports.

        Args:
            namespace (Namespace): The imported namespace.
            imported_alias (bool): Set if this namespace references an alias
                in the imported namespace.
            imported_data_type (bool): Set if this namespace references a
                data type in the imported namespace.
            imported_annotation (bool): Set if this namespace references a
                annotation in the imported namespace.
            imported_annotation_type (bool): Set if this namespace references an
                annotation in the imported namespace, possibly indirectly (by
                referencing an annotation elsewhere that has this type).
        """
        assert self.name != namespace.name, "Namespace cannot import itself."
        reason = self._imported_namespaces.setdefault(namespace, _ImportReason())
        if imported_alias:
            reason.alias = True
        if imported_data_type:
            reason.data_type = True
        if imported_annotation:
            reason.annotation = True
        if imported_annotation_type:
            reason.annotation_type = True

    def linearize_data_types(self) -> typing.List[UserDefined]:
        """
        Returns a list of all data types used in the namespace. Because the
        inheritance of data types can be modeled as a DAG, the list will be a
        linearization of the DAG. It's ideal to generate data types in this
        order so that composite types that reference other composite types are
        defined in the correct order.
        """
        linearized_data_types = []
        seen_data_types: typing.Set[UserDefined] = set()

        def add_data_type(data_type: UserDefined) -> None:
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

    def linearize_aliases(self) -> typing.List[Alias]:
        """
        Returns a list of all aliases used in the namespace. The aliases are
        ordered to ensure that if they reference other aliases those aliases
        come earlier in the list.
        """
        linearized_aliases = []
        seen_aliases: typing.Set[Alias] = set()

        def add_alias(alias: Alias) -> None:
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

    def get_route_io_data_types(self) -> typing.List[UserDefined]:
        """
        Returns a list of all user-defined data types that are referenced as
        either an argument, result, or error of a route. If a List or Nullable
        data type is referenced, then the contained data type is returned
        assuming it's a user-defined type.
        """
        data_types: typing.Set[UserDefined] = set()
        for route in self.routes:
            data_types |= self.get_route_io_data_types_for_route(route)
        return sorted(data_types, key=lambda dt: dt.name)

    def get_route_io_data_types_for_route(
        self, route: "ApiRoute"
    ) -> typing.Set[UserDefined]:
        """
        Given a route, returns a set of its argument/result/error datatypes.
        """
        data_types: typing.Set[UserDefined] = set()
        for dtype in (
            route.arg_data_type,
            route.result_data_type,
            route.error_data_type,
        ):
            while is_list_type(dtype) or is_nullable_type(dtype):
                data_list_type: typing.Any = dtype
                dtype = data_list_type.data_type
            if is_composite_type(dtype) or is_alias(dtype):
                data_user_type: typing.Any = dtype
                data_types.add(data_user_type)
        return data_types

    def get_imported_namespaces(
        self,
        must_have_imported_data_type: bool = False,
        consider_annotations: bool = False,
        consider_annotation_types: bool = False,
    ) -> typing.List["ApiNamespace"]:
        """
        Returns a list of Namespace objects. A namespace is a member of this
        list if it is imported by the current namespace and a data type is
        referenced from it. Namespaces are in ASCII order by name.

        Args:
            must_have_imported_data_type (bool): If true, result does not
                include namespaces that were not imported for data types.
            consider_annotations (bool): If false, result does not include
                namespaces that were only imported for annotations
            consider_annotation_types (bool): If false, result does not
                include namespaces that were only imported for annotation types.

        Returns:
            List[Namespace]: A list of imported namespaces.
        """
        imported_namespaces = []
        for imported_namespace, reason in self._imported_namespaces.items():
            if must_have_imported_data_type and not reason.data_type:
                continue
            if (not consider_annotations) and not (
                reason.data_type or reason.alias or reason.annotation_type
            ):
                continue
            if (not consider_annotation_types) and not (
                reason.data_type or reason.alias or reason.annotation
            ):
                continue

            imported_namespaces.append(imported_namespace)
        imported_namespaces.sort(key=lambda n: n.name)
        return imported_namespaces

    def get_namespaces_imported_by_route_io(self) -> typing.List["ApiNamespace"]:
        """
        Returns a list of Namespace objects. A namespace is a member of this
        list if it is imported by the current namespace and has a data type
        from it referenced as an argument, result, or error of a route.
        Namespaces are in ASCII order by name.
        """
        namespace_data_types = sorted(
            self.get_route_io_data_types(), key=lambda dt: dt.name
        )
        referenced_namespaces = set()
        for data_type in namespace_data_types:
            if data_type.namespace != self:
                referenced_namespaces.add(data_type.namespace)
        return sorted(referenced_namespaces, key=lambda n: n.name)

    def normalize(self) -> None:
        """
        Alphabetizes routes to make route declaration order irrelevant.
        """
        self.routes.sort(key=lambda route: route.name)
        self.data_types.sort(key=lambda data_type: data_type.name)
        self.aliases.sort(key=lambda alias: alias.name)
        self.annotations.sort(key=lambda annotation: annotation.name)

    def __repr__(self) -> str:
        return f"ApiNamespace({self.name!r})"


class ApiRoute:
    """
    Represents an API endpoint.
    """

    def __init__(
        self, name: typing.Text, version: int, ast_node: typing.Optional[AstRouteDef]
    ) -> None:
        """
        :param str name: Designated name of the endpoint.
        :param int version: Designated version of the endpoint.
        :param ast_node: Raw route definition from the parser.
        """
        self.name = name
        self.version = version
        self._ast_node = ast_node

        # These attributes are set later by set_attributes()
        self.deprecated: typing.Optional[DeprecationInfo] = None
        self.raw_doc: typing.Optional[typing.Text] = None
        self.doc: typing.Optional[typing.Text] = None
        self.arg_data_type: typing.Optional[DataType] = None
        self.result_data_type: typing.Optional[DataType] = None
        self.error_data_type: typing.Optional[DataType] = None
        self.attrs: typing.Optional[typing.Mapping[typing.Text, typing.Any]] = None

    def set_attributes(
        self, deprecated, doc, arg_data_type, result_data_type, error_data_type, attrs
    ):
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

    def name_with_version(self):
        """
        Get user-friendly representation of the route.

        :return: Route name with version suffix. The version suffix is omitted for version 1.
        """
        if self.version == 1:
            return self.name
        else:
            return f"{self.name}:{self.version}"

    def __repr__(self):
        return f"ApiRoute({self.name_with_version()})"


class DeprecationInfo:
    def __init__(self, by: typing.Optional[ApiRoute] = None) -> None:
        """
        :param ApiRoute by: The route that replaces this deprecated one.
        """
        assert by is None or isinstance(by, ApiRoute), repr(by)
        self.by = by


class ApiRoutesByVersion:
    """
    Represents routes of different versions for a common name.
    """

    def __init__(self) -> None:
        """
        :param at_version: The dict mapping a version number to a route.
        """
        self.at_version: typing.Dict[int, ApiRoute] = {}
