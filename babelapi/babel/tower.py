from collections import defaultdict
import copy
import inspect
import logging
import os
import re

from babelapi.babel.parser import BabelParser
from babelapi.data_type import (
    Binary,
    Boolean,
    DataType,
    StructField,
    UnionField,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    ParameterError,
    String,
    Struct,
    TagRef,
    Timestamp,
    UInt32,
    UInt64,
    Union,
    Void,
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
    BabelVoidField,
    BabelTagRef,
    BabelTypeDef,
    BabelTypeRef,
)

class InvalidSpec(Exception): pass

# Patterns for references in documentation
doc_ref_re = re.compile(r':(?P<tag>[A-z]+):`(?P<val>.*?)`')
doc_ref_val_re = re.compile(
    r'^(null|true|false|-?\d+(\.\d*)?(e-?\d+)?|"[^\\"]*")$')

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
        Void,
    ]

    default_env = {data_type.__name__: data_type for data_type in data_types}

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
        # Map of namespace name (str) -> environment (dict)
        self.env_by_namespace = {}
        # Map of namespace name (str) ->  set of paths to parsed headers
        self.includes_by_namespace = defaultdict(set)

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
            raise InvalidSpec(
                'Line %d: Symbol %r already defined on line %d.' %
                (item.lineno, item.name, env[item.name]._token.lineno))
        elif item.type_ref.name not in env:
            raise InvalidSpec('Line %d: Symbol %r is undefined.' %
                              (item.lineno, item.type_ref.name))

        obj = env[item.type_ref.name]
        if inspect.isclass(obj):
            env[item.name] = self._instantiate_data_type(
                obj, item.type_ref.args, item.lineno)
        elif isinstance(obj, ApiRoute):
            raise InvalidSpec('Line %d: Cannot alias a route.' % item.lineno)
        elif item.type_ref.args[0] or item.type_ref.args[1]:
            # An instance of a type cannot have any additional
            # attributes specified.
            raise InvalidSpec('Line %d: Attributes cannot be specified for '
                              'instantiated type %r.' %
                              (item.lineno, item.type_ref.name))
        else:
            ref = env[item.type_ref.name]
            if item.type_ref.nullable:
                ref = copy.copy(ref)
                ref.nullable = item.type_ref.nullable
            env[item.name] = ref

    def _create_type(self, env, item):
        if item.name in env:
            # TODO(kelkabany): This reports the wrong line number for the
            # original definition if an alias was the source of the name
            # conflict. It reports the line the aliased type was defined,
            # rather than the alias itself. Since aliases aren't tracked in
            # the environment, fixing this will require a refactor.
            raise InvalidSpec(
                'Line %d: Symbol %r already defined on line %d.' %
                (item.lineno, item.name, env[item.name]._token.lineno))
        if item.composite_type == 'struct':
            supertype = None
            if item.extends:
                if item.extends not in env:
                    raise InvalidSpec('Line %d: Data type %r is undefined.' %
                                      (item.lineno, item.extends))
                else:
                    supertype = env.get(item.extends)
            api_type_fields = []
            for babel_field in item.fields:
                api_type_field = self._create_struct_field(env, babel_field)
                api_type_fields.append(api_type_field)
            api_type = Struct(item.name, item.doc, api_type_fields, item,
                              supertype, item.coverage)
        elif item.composite_type == 'union':
            subtype = None
            if item.extends:
                if item.extends not in env:
                    raise InvalidSpec('Line %d: Data type %r is undefined.' %
                                      (item.lineno, item.extends))
                else:
                    subtype = env.get(item.extends)
            api_type_fields = []
            catch_all_field = None
            for babel_field in item.fields:
                api_type_field = self._create_union_field(env, babel_field)
                if (isinstance(babel_field, BabelVoidField)
                        and babel_field.catch_all):
                    if catch_all_field is not None:
                        raise InvalidSpec('Line %d: Only one catch-all tag '
                                          'per Union.' % babel_field.lineno)

                    # Verify that no subtype already has a catch-all tag.
                    # Do this here so that we still have access to line nums.
                    cur_subtype = subtype
                    while cur_subtype:
                        if cur_subtype.catch_all_field:
                            raise InvalidSpec('Line %d: Subtype %r already '
                                'declared a catch-all tag.' %
                                (babel_field.lineno, cur_subtype.name))
                        cur_subtype = cur_subtype.subtype

                    catch_all_field = api_type_field
                api_type_fields.append(api_type_field)

            api_type = Union(item.name, item.doc, api_type_fields, item,
                             subtype, catch_all_field)
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
            if isinstance(data_type, Void):
                raise InvalidSpec('Line %d: Struct field %r cannot have a '
                                  'Void type.' %
                                  (babel_field.lineno, babel_field.name))
            elif data_type.nullable and babel_field.has_default:
                raise InvalidSpec('Line %d: Field %r cannot be a nullable '
                                  'type and have a default specified.' %
                                  (babel_field.lineno, babel_field.name))
            api_type_field = StructField(
                babel_field.name,
                data_type,
                babel_field.doc,
                babel_field,
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
        if isinstance(babel_field, BabelVoidField):
            api_type_field = UnionField(babel_field.name, Void(),
                                        babel_field.doc, babel_field)
        elif babel_field.type_ref.name not in env:
            raise InvalidSpec('Line %d: Symbol %r is undefined.' %
                              (babel_field.lineno, babel_field.type_ref.name))
        else:
            data_type = self._resolve_type(
                env,
                babel_field.type_ref,
            )
            if isinstance(data_type, Void):
                raise InvalidSpec('Line %d: Union member %r cannot have Void '
                                  'type explicit, omit Void instead.' %
                                  (babel_field.lineno, babel_field.name))
            api_type_field = UnionField(
                babel_field.name,
                data_type,
                babel_field.doc,
                babel_field,
            )
        return api_type_field

    def _instantiate_data_type(self, data_type_class, data_type_args, lineno):
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

        pos_args, kw_args = data_type_args

        if (num_args - num_defaults) > len(pos_args):
            # Report if a positional argument is missing
            raise InvalidSpec(
                'Line %d: Missing positional argument %r for %s type' %
                (lineno, argspec.args[len(pos_args)],
                 data_type_class.__name__))
        elif (num_args - num_defaults) < len(pos_args):
            # Report if there are too many positional arguments
            raise InvalidSpec(
                'Line %d: Too many positional arguments for %s type' %
                (lineno, data_type_class.__name__)
            )

        # Map from arg name to bool indicating whether the arg has a default
        args = {}
        for i, key in enumerate(argspec.args):
            args[key] = (i >= num_args - num_defaults)

        for key in kw_args:
            # Report any unknown keyword arguments
            if key not in args:
                raise InvalidSpec('Line %d: Unknown argument %r to %s type' %
                    (lineno, key, data_type_class.__name__))
            # Report any positional args that are defined as keywords args.
            if not args[key]:
                raise InvalidSpec(
                    'Line %d: Positional argument %r cannot be specified as a '
                    'keyword argument' % (lineno, key))
            del args[key]

        try:
            return data_type_class(*pos_args, **kw_args)
        except ParameterError as e:
            # Each data type validates its own attributes, and will raise a
            # ParameterError if the type or value is bad.
            raise InvalidSpec('Line %d: Bad argument to %s type: %s' %
                              (lineno, data_type_class.__name__, e.args[0]))

    def _resolve_type(self, env, type_ref):
        """Resolves the data type referenced by type_ref."""
        obj = env[type_ref.name]
        if obj is Void and type_ref.nullable:
            raise InvalidSpec('Line %d: Void cannot be marked nullable.' %
                              type_ref.lineno)
        elif inspect.isclass(obj):
            resolved_data_type_args = self._resolve_args(env, type_ref.args)
            data_type = self._instantiate_data_type(
                obj, resolved_data_type_args, type_ref.lineno)
            data_type.nullable = type_ref.nullable
        elif isinstance(obj, ApiRoute):
            raise InvalidSpec('Line %d: A route is not a valid field type.' %
                              type_ref.lineno)
        elif type_ref.args[0] or type_ref.args[1]:
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

    def _resolve_args(self, env, args):
        """
        Resolves type references in data type arguments to data types in
        the environment.
        """
        pos_args, kw_args = args

        def check_value(v):
            if isinstance(v, BabelTypeRef):
                if v.name not in env:
                    raise InvalidSpec('Line %d: Symbol %r is undefined' %
                                      (v.lineno, v.name))
                else:
                    return self._resolve_type(env, v)
            else:
                return v

        new_pos_args = [check_value(pos_arg) for pos_arg in pos_args]
        new_kw_args = {k: check_value(v) for k, v in kw_args.iteritems()}
        return new_pos_args, new_kw_args

    def _create_route(self, env, item):
        """
        Constructs a route and adds it to the environment.

        Args:
            env (dict): The environment of defined symbols. A new key is added
                corresponding to the name of this new route.
            item (BabelRouteDef): Raw route definition from the parser.

        Returns:
            babelapi.api.ApiRoute: A fully-defined route.
        """
        if item.name in env:
            raise InvalidSpec(
                'Line %d: Symbol %r already defined on line %d.' %
                (item.lineno, item.name, env[item.name]._token.lineno))
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
            item,
        )
        env[route.name] = route
        return route

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
        # Keep lists of all the types and routes added just from this spec.
        data_types = []
        routes = []
        # Because there might have already been a spec that was part of this
        # same namespace, the environment might already exist.
        if namespace.name in self.env_by_namespace:
            env = self.env_by_namespace[namespace.name]
        else:
            env = copy.copy(self.default_env)
            self.env_by_namespace[namespace.name] = env

        for item in desc:
            if isinstance(item, BabelInclude):
                # Only re-parse and include the header for this namespace if
                # we haven't already done so.
                full_path = os.path.join(os.path.dirname(path), item.target)
                if full_path not in self.includes_by_namespace[namespace.name]:
                    self._include_babelh(namespace, env, os.path.dirname(path),
                                         item.target)
                    self.includes_by_namespace[namespace.name] = full_path
                    self._logger.info(
                        'Done parsing header spec, resuming parsing %s',
                        os.path.basename(path))
            elif isinstance(item, BabelAlias):
                self._create_alias(env, item)
            elif isinstance(item, BabelTypeDef):
                api_type = self._create_type(env, item)
                data_types.append(api_type)
                namespace.add_data_type(api_type)
            elif isinstance(item, BabelRouteDef):
                route = self._create_route(env, item)
                routes.append(route)
                namespace.add_route(route)
            else:
                raise AssertionError('Unknown Babel Declaration Type %r' %
                                     item.__class__.__name__)

        # Validate the doc refs of each api entity that has a doc
        for data_type in data_types:
            if data_type.doc:
                self._validate_doc_refs(
                    env, data_type.doc, data_type._token.lineno + 1)
            for field in data_type.fields:
                if field.doc:
                    self._validate_doc_refs(
                        env, field.doc, field._token.lineno + 1, data_type)
        for route in routes:
            if route.doc:
                self._validate_doc_refs(
                    env, route.doc, route._token.lineno + 1)

        # Coverage is specified as a forward declaration so here's where we
        # resolve the symbols.
        for data_type in namespace.data_types:
            if isinstance(data_type, Struct) and data_type.has_coverage():
                data_type.resolve_coverage(env)
        # TODO(kelkabany): Check to make sure that no other type that is not
        # covered extends a data type that enforces coverage.

    def _include_babelh(self, namespace, env, path, name):
        babelh_path = os.path.join(path, name) + '.babelh'
        if not os.path.exists(babelh_path):
            raise InvalidSpec('Babel header %r does not exist.' % babelh_path)

        self._logger.info("Parsing included header spec '%s'" % name)

        with open(babelh_path) as f:
            scripture = f.read()

        desc = self.parser.parse(scripture)

        for item in desc[:]:
            if isinstance(item, BabelAlias):
                self._create_alias(env, item)
            elif isinstance(item, BabelTypeDef):
                api_type = self._create_type(env, item)
                namespace.add_data_type(api_type)
            elif isinstance(item, BabelInclude):
                raise InvalidSpec(
                    "Line %d: Cannot use 'include' in header spec." %
                    item.lineno)
            elif isinstance(item, BabelRouteDef):
                raise InvalidSpec(
                    'Line %d: Cannot define route in header spec.' %
                    item.lineno)
            else:
                raise AssertionError('Unknown Babel Declaration Type %r' %
                                     item.__class__.__name__)

    def _validate_doc_refs(self, env, doc, lineno, type_context=None):
        """
        Validates that all the documentation references in a docstring are
        formatted properly, have valid values, and make references to valid
        symbols.

        Args:
            env (dict): The environment of defined symbols.
            doc (str): The docstring to validate.
            lineno (int): The line number the docstring begins on in the spec.
            type_context (babelapi.data_type.CompositeType): If the docstring
                belongs to a user-defined type (Struct or Union) or one of its
                fields, set this to the type. This is needed for "field" doc
                refs that don't name a type to be validated.
        """
        for match in doc_ref_re.finditer(doc):
            tag = match.group('tag')
            val = match.group('val')
            if tag == 'field':
                if '.' in val:
                    type_name, field_name = val.split('.', 1)
                    if type_name not in env:
                        raise InvalidSpec(
                            'Line %d: Bad doc reference to field %s of '
                            'unknown type %r.' %
                            (lineno, field_name, type_name))
                    elif isinstance(env[type_name], ApiRoute):
                        raise InvalidSpec(
                            'Line %d: Bad doc reference to field %s of '
                            'route %r.' %
                            (lineno, field_name, type_name))
                    elif not any(field.name == field_name
                                 for field in env[type_name].all_fields):
                        raise InvalidSpec(
                            'Line %d: Bad doc reference to unknown field %r.' %
                            (lineno, val))
                else:
                    # Referring to a field that's a member of this type
                    assert type_context is not None
                    if not any(field.name == val
                               for field in type_context.all_fields):
                        raise InvalidSpec(
                            'Line %d: Bad doc reference to unknown field %r.' %
                            (lineno, val))
            elif tag == 'link':
                if not (1 < val.rfind(' ') < len(val) - 1):
                    # There must be a space somewhere in the middle of the
                    # string to separate the title from the uri.
                    raise InvalidSpec(
                        'Line %d: Bad doc reference to link (need a title and '
                        'uri separated by a space): %r.' %
                        (lineno, val))
            elif tag == 'route':
                if val not in env:
                    raise InvalidSpec(
                        'Line %d: Unknown doc reference to route %r.' %
                        (lineno, val))
                elif not isinstance(env[val], ApiRoute):
                    raise InvalidSpec('Line %d: Doc reference to type %r is '
                        'not a struct or union.' % (lineno, val))
            elif tag == 'type':
                if val not in env:
                    raise InvalidSpec(
                        'Line %d: Unknown doc reference to type %r.' %
                        (lineno, val))
                elif not isinstance(env[val], (Struct, Union)):
                    raise InvalidSpec('Line %d: Documentation reference to '
                        'type %r is not a struct or union.' % (lineno, val))
            elif tag == 'val':
                if not doc_ref_val_re.match(val):
                    raise InvalidSpec(
                        'Line %d: Bad doc reference value %r.' %
                        (lineno, val))
            else:
                raise InvalidSpec(
                    'Line %d: Unknown doc reference tag %r.' %
                    (lineno, tag))
