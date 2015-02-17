import copy
import inspect
import logging
import os

from babelapi.babel.parser import BabelParser
from babelapi.data_type import (
    Any,
    Binary,
    Boolean,
    DataType,
    Empty,
    StructField,
    UnionField,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    Null,
    ParameterError,
    String,
    Struct,
    Symbol,
    TagRef,
    Timestamp,
    UInt32,
    UInt64,
    Union,
)
from babelapi.api import (
    Api,
    ApiRoute,
)
from babelapi.babel.parser import (
    BabelAlias,
    BabelInclude,
    BabelNamespace,
    BabelRouteDef,
    BabelSymbolField,
    BabelTagRef,
    BabelTypeDef,
    BabelTypeRef,
)

class InvalidSpec(Exception): pass

class TowerOfBabel(object):

    data_types = [
        Binary,
        Boolean,
        Float32,
        Float64,
        Int32,
        Int64,
        List,
        String,
        Struct,
        Timestamp,
        UInt32,
        UInt64,
        Union,
    ]

    default_env = {data_type.__name__: data_type for data_type in data_types}
    default_env['Any'] = Any()
    default_env['Empty'] = Empty
    default_env['Null'] = Null()

    # FIXME: Version should not have a default.
    def __init__(self, paths, version='0.1b1', debug=False):
        """Creates a new tower of babel."""

        self._debug = debug
        self._logger = logging.getLogger('babelapi.idl')

        self.api = Api(version=version)

        # A list of all (path, raw text) of API descriptions
        self._scriptures = []
        for path in paths:
            with open(path) as f:
                scripture = f.read()
                self._scriptures.append((path, scripture))

        self.parser = BabelParser(debug=debug)

    def parse(self):
        """Parses each Babel file and returns an API description. Returns None
        if an error was encountered during parsing."""
        for path, scripture in self._scriptures:
            self._logger.info('Parsing spec %s', path)
            res = self.parse_scripture(scripture)
            if self.parser.got_errors_parsing():
                for error in self.parser.get_error_strings():
                    self._logger.error(error)
                return None
            elif res:
                self.add_to_api(path, res)
            else:
                self._logger.warn('No output generated from file')
        return self.api

    def parse_scripture(self, scripture):
        """Parses a single Babel file."""
        if self._debug:
            self.parser.test_lexing(scripture)

        return self.parser.parse(scripture)

    def _create_alias(self, env, item):
        if item.name in env:
            raise InvalidSpec('Line %d: Symbol %r already defined.' %
                              (item.lineno, item.name))
        elif item.type_ref.name not in env:
            raise InvalidSpec('Line %d: Symbol %r is undefined.' %
                              (item.lineno, item.type_ref.name))

        obj = env[item.type_ref.name]
        if inspect.isclass(obj):
            env[item.name] = self._instantiate_data_type(
                obj, dict(item.type_ref.attrs), item.lineno)
        elif item.type_ref.attrs:
            # An instance of a type cannot have any additional
            # attributes specified.
            raise InvalidSpec('Line %d: Attributes cannot be specified for'
                              'instantiated type %r.' %
                              (item.lineno, item.type_ref.name))
        else:
            ref = env[item.type_ref.name]
            if item.type_ref.nullable:
                ref = copy.copy(ref)
                ref.nullable = item.type_ref.nullable
            env[item.name] = ref

    def _create_type(self, env, item):
        super_type = None
        if item.composite_type == 'struct':
            if item.extends:
                if item.extends not in env:
                    raise InvalidSpec('Line %d: Data type %r is undefined.' %
                                      (item.lineno, item.extends))
                else:
                    super_type = env.get(item.extends)
            api_type_fields = []
            for babel_field in item.fields:
                api_type_field = self._create_struct_field(env, babel_field)
                api_type_fields.append(api_type_field)
            api_type = Struct(item.name, item.doc, api_type_fields, super_type, item.coverage)
        elif item.composite_type == 'union':
            api_type_fields = []
            catch_all_field = None
            for babel_field in item.fields:
                api_type_field = self._create_union_field(env, babel_field)
                if isinstance(babel_field, BabelSymbolField) and babel_field.catch_all:
                    if catch_all_field is not None:
                        raise InvalidSpec('Line %d: Only one catch all symbol '
                                          'per Union.' % babel_field.lineno)
                    catch_all_field = api_type_field
                api_type_fields.append(api_type_field)
            api_type = Union(item.name, item.doc, api_type_fields, super_type,
                             catch_all_field)
        else:
            raise AssertionError('Unknown composite_type %r' %
                                 item.composite_type)
        for example_label, (example_text, example) in item.examples.items():
            api_type.add_example(example_label, example_text, dict(example))
        env[item.name] = api_type
        return api_type

    def _create_struct_field(self, env, babel_field):
        """
        This function resolves symbols to objects that we've instantiated in
        the current environment. For example, a field with data type named
        "String" is pointed to a String() object.

        The caller needs to ensure that this babel_field is for a Struct and not
        for a Union.

        Returns:
            babelapi.data_type.StructField: A field of a struct.
        """
        if babel_field.type_ref.name not in env:
            raise InvalidSpec('Line %d: Symbol %r is undefined.' %
                              (babel_field.lineno, babel_field.type_ref.name))
        else:
            data_type = self._resolve_type(env, babel_field.type_ref)
            if data_type.nullable and babel_field.has_default:
                raise InvalidSpec('Line %d: Field %r cannot be a nullable '
                                  'type and have a default specified.' %
                                  (babel_field.lineno, babel_field.name))
            api_type_field = StructField(
                babel_field.name,
                data_type,
                babel_field.doc,
                deprecated=babel_field.deprecated,
            )
            if babel_field.has_default:
                if isinstance(babel_field.default, BabelTagRef):
                    if babel_field.default.union_name is not None:
                        raise InvalidSpec('Line %d: Field %r has a qualified '
                            'default which is unnecessary since the type %r '
                            'is known' % (babel_field.lineno, babel_field.name,
                                          babel_field.default.union_name))
                    default_value = TagRef(data_type, babel_field.default.tag)
                else:
                    default_value = babel_field.default
                if not (babel_field.type_ref.nullable and default_value is None):
                    # Verify that the type of the default value is correct for this field
                    try:
                        data_type.check(default_value)
                    except ValueError as e:
                        raise InvalidSpec('Line %d: Field %r has an invalid '
                            'default: %s' % (babel_field.lineno,
                                             babel_field.name, e))
                api_type_field.set_default(default_value)
        return api_type_field

    def _create_union_field(self, env, babel_field):
        """
        This function resolves symbols to objects that we've instantiated in
        the current environment. For example, a field with data type named
        "String" is pointed to a String() object.

        The caller needs to ensure that this babel_field is for a Union and not
        for a Struct.

        Returns:
            babelapi.data_type.UnionField: A field of a union.
        """
        if isinstance(babel_field, BabelSymbolField):
            api_type_field = UnionField(babel_field.name, Symbol(), babel_field.doc)
        elif babel_field.type_ref.name not in env:
            raise InvalidSpec('Line %d: Symbol %r is undefined.' %
                              (babel_field.lineno, babel_field.type_ref.name))
        else:
            data_type = self._resolve_type(
                env,
                babel_field.type_ref,
            )
            api_type_field = UnionField(
                babel_field.name,
                data_type,
                babel_field.doc,
            )
        return api_type_field

    def _instantiate_data_type(self, data_type_class, data_type_attrs, lineno):
        """
        Responsible for instantiating a data type with additional attributes.
        This method ensures that the specified attributes are valid.

        Args:
            data_type_class (DataType): The class to instantiate.
            data_type_attrs (dict): A map from str -> values of attributes.
                These will be passed into the constructor of data_type_class
                as keyword arguments.

        Returns:
            babelapi.data_type.DataType: A parameterized instance.
        """
        assert issubclass(data_type_class, DataType), \
            'Expected babelapi.data_type.DataType, got %r' % data_type_class

        argspec = inspect.getargspec(data_type_class.__init__)
        argspec.args.remove('self')
        num_args = len(argspec.args)
        # Unfortunately, argspec.defaults is None if there are no defaults
        num_defaults = len(argspec.defaults or ())

        # Map from arg name to bool indicating whether the arg has a default
        args = {}
        for i, key in enumerate(argspec.args):
            args[key] = (i >= num_args - num_defaults)

        # Report any unknown arguments
        for key in data_type_attrs:
            if key not in args:
                raise InvalidSpec('Line %d: Unknown argument %r to %s type' %
                    (lineno, key, data_type_class.__name__))
            del args[key]

        # Report any missing arguments
        for key in args:
            if not args[key]:
                raise InvalidSpec('Line %d: Missing argument %r for %s type' %
                    (lineno, argspec.args[0], data_type_class.__name__))

        try:
            return data_type_class(**data_type_attrs)
        except ParameterError as e:
            # Each data type validates its own attributes, and will raise a
            # ParameterError if the type or value is bad.
            raise InvalidSpec('Line %d: Bad argument to %s type: %s' %
                              (lineno, data_type_class.__name__, e.args[0]))

    def _resolve_type(self, env, type_ref):
        """Resolves the data type referenced by type_ref."""
        obj = env[type_ref.name]
        if inspect.isclass(obj):
            resolved_data_type_attrs = self._resolve_attrs(env, type_ref.attrs)
            data_type = self._instantiate_data_type(
                obj, dict(resolved_data_type_attrs), type_ref.lineno)
            data_type.nullable = type_ref.nullable
        elif type_ref.attrs:
            # An instance of a type cannot have any additional
            # attributes specified.
            raise InvalidSpec('Line %d: Attributes cannot be specified for '
                              'instantiated type %r.' %
                              (type_ref.lineno, type_ref.name))
        else:
            # The data_type could be nullable if this is an alias to a nullable
            # type. Or, the type reference itself could be nullable.
            data_type = env[type_ref.name]
            if data_type.nullable or type_ref.nullable:
                data_type = copy.copy(data_type)
                data_type.nullable = True
        return data_type

    def _resolve_attrs(self, env, attrs):
        """
        Resolves type references in data type attributes to data types in
        the environment.
        """
        new_attrs = []
        for (k, v) in attrs:
            if isinstance(v, BabelTypeRef):
                if v.name not in env:
                    raise InvalidSpec('Line %d: Symbol %r is undefined' %
                                      (v.lineno, v.name))
                else:
                    new_attr = (k, self._resolve_type(env, v))
                    new_attrs.append(new_attr)
            else:
                new_attrs.append((k, v))
        return new_attrs

    def add_to_api(self, path, desc):

        if isinstance(desc[0], BabelNamespace):
            namespace_decl = desc.pop(0)
        else:
            if self._debug:
                self._logger.info('Description: %r' % desc)
            raise InvalidSpec('Line %d: First declaration in a babel must be '
                              'a namespace. Possibly caused by preceding '
                              'errors.' % desc[0].lineno)

        namespace = self.api.ensure_namespace(namespace_decl.name)
        env = copy.copy(self.default_env)

        for item in desc:
            if isinstance(item, BabelInclude):
                self._include_babelh(env, os.path.dirname(path), item.target)
            elif isinstance(item, BabelAlias):
                self._create_alias(env, item)
            elif isinstance(item, BabelTypeDef):
                api_type = self._create_type(env, item)
                namespace.add_data_type(api_type)
            elif isinstance(item, BabelRouteDef):
                request_data_type = self._resolve_type(env, item.request_type_ref)
                response_data_type = self._resolve_type(env, item.response_type_ref)
                error_data_type = self._resolve_type(env, item.error_type_ref)
                route = ApiRoute(
                    item.name,
                    item.doc,
                    request_data_type,
                    response_data_type,
                    error_data_type,
                    item.attrs,
                )
                namespace.add_route(route)
            else:
                raise AssertionError('Unknown Babel Declaration Type %r' %
                                     item.__class__.__name__)

        # Coverage is specified as a forward declaration so here's where we
        # resolve the symbols.
        for data_type in namespace.data_types:
            if isinstance(data_type, Struct) and data_type.has_coverage():
                data_type.resolve_coverage(env)
        # TODO(kelkabany): Check to make sure that no other type that is not
        # covered extends a data type that enforces coverage.

    def _include_babelh(self, env, path, name):
        babelh_path = os.path.join(path, name) + '.babelh'
        if not os.path.exists(babelh_path):
            raise InvalidSpec('Babel header %r does not exist.' % babelh_path)

        with open(babelh_path) as f:
            scripture = f.read()

        desc = self.parser.parse(scripture)

        for item in desc[:]:
            if isinstance(item, BabelInclude):
                self._include_babelh(env, os.path.dirname(path), item.target)
            elif isinstance(item, BabelAlias):
                self._create_alias(env, item)
            elif isinstance(item, BabelTypeDef):
                self._create_type(env, item)
            else:
                raise AssertionError('Unknown Babel Declaration Type %r' %
                                     item.__class__.__name__)
