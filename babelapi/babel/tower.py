import copy
import inspect
import logging
import os
import sys

from babelapi.babel.parser import BabelParser
from babelapi.data_type import (
    Any,
    Binary,
    Boolean,
    Empty,
    StructField,
    UnionField,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    Null,
    String,
    Struct,
    Symbol,
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
    BabelSymbol,
    BabelSymbolField,
    BabelTypeDef,
)

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
            raise Exception('Symbol %r already defined' % item.name)
        elif item.data_type_name not in env:
            raise Exception('Symbol %r is undefined' % item.data_type_name)

        obj = env[item.data_type_name]
        if inspect.isclass(obj):
            env[item.name] = obj(**dict(item.data_type_attrs))
        elif item.data_type_attrs:
            # An instance of a type cannot have any additional
            # attributes specified.
            raise Exception('Attributes cannot be specified for instantiated '
                            'type %r.' % item.data_type_name)
        else:
            env[item.name] = env[item.data_type_name]

    def _create_type(self, env, item):
        super_type = None
        if item.composite_type == 'struct':
            if item.extends:
                if item.extends not in env:
                    raise Exception('Data type %r is undefined' % item.extends)
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
                    assert not catch_all_field, 'Only one catch all symbol per Union.'
                    catch_all_field = api_type_field
                api_type_fields.append(api_type_field)
            api_type = Union(item.name, item.doc, api_type_fields, super_type,
                             catch_all_field)
        else:
            raise ValueError('Unknown composite_type %r'
                             % item.composite_type)
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

        Returns a babelapi.data_type.StructField object.
        """
        if babel_field.data_type_name not in env:
            raise Exception('Symbol %r is undefined' % babel_field.data_type_name)
        else:
            data_type = self._resolve_type(
                env,
                babel_field.data_type_name,
                babel_field.data_type_attrs,
            )
            api_type_field = StructField(
                babel_field.name,
                data_type,
                babel_field.doc,
                optional=babel_field.optional,
                deprecated=babel_field.deprecated,
            )
            if babel_field.has_default:
                if not (babel_field.optional and babel_field.default is None):
                    # Verify that the type of the default value is correct for this field
                    data_type.check(babel_field.default)
                api_type_field.set_default(babel_field.default)
        return api_type_field

    def _create_union_field(self, env, babel_field):
        """
        This function resolves symbols to objects that we've instantiated in
        the current environment. For example, a field with data type named
        "String" is pointed to a String() object.

        The caller needs to ensure that this babel_field is for a Union and not
        for a Struct.

        Returns a babelapi.data_type.UnionField object.
        """
        if isinstance(babel_field, BabelSymbolField):
            api_type_field = UnionField(babel_field.name, Symbol(), babel_field.doc)
        elif babel_field.data_type_name not in env:
            raise Exception('Symbol %r is undefined' % babel_field.data_type_name)
        else:
            data_type = self._resolve_type(
                env,
                babel_field.data_type_name,
                babel_field.data_type_attrs,
            )
            api_type_field = UnionField(
                babel_field.name,
                data_type,
                babel_field.doc,
            )
        return api_type_field

    def _resolve_type(self, env, data_type_name, data_type_attrs):
        """
        Resolves the data type referenced by the data_type_name.
        """
        obj = env[data_type_name]
        if inspect.isclass(obj):
            resolved_data_type_attrs = self._resolve_attrs(env, data_type_attrs)
            data_type = obj(**dict(resolved_data_type_attrs))
        elif data_type_attrs:
            # An instance of a type cannot have any additional
            # attributes specified.
            raise Exception('Attributes cannot be specified for instantiated '
                            'type %r.' % data_type_name)
        else:
            data_type = env[data_type_name]
        return data_type

    def _resolve_attrs(self, env, attrs):
        """
        Resolves symbols in data type attributes to data types in environment.
        """
        new_attrs = []
        for (k, v) in attrs:
            if isinstance(v, BabelSymbol):
                if v.name not in env:
                    raise Exception('Symbol %r is undefined' % v.name)
                else:
                    new_attr = (k, self._resolve_type(env, v.name, []))
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
            self._logger.error('First declaration in a babel must be a '
                               'namespace. Possibly caused by preceding '
                               'errors.')
            sys.exit(1)

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
                request_data_type = self._resolve_data_type(
                    env,
                    item.request_data_type_name,
                )
                response_data_type = self._resolve_data_type(
                    env,
                    item.response_data_type_name,
                )
                error_data_type = self._resolve_data_type(
                    env,
                    item.error_data_type_name,
                )
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
                raise Exception('Unknown Babel Declaration Type %r'
                                % item.__class__.__name__)

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
            raise Exception('Babel header %r does not exist'
                            % babelh_path)

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
                raise Exception('Unknown Babel Declaration Type %r'
                                % item.__class__.__name__)

    def _resolve_data_type(self, env, data_type_name):
        if not data_type_name:
            # FIXME: We should think through whether the name should always be present
            return None
        if data_type_name not in env:
            raise Exception('Symbol %r is undefined' % data_type_name)
        data_type = env.get(data_type_name)
        return data_type
