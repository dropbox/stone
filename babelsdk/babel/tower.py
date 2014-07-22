import copy
import inspect
import logging
import os
import sys

from babelsdk.babel.parser import BabelParser
from babelsdk.data_type import (
    Binary,
    Boolean,
    Field,
    Float,
    Int32,
    Int64,
    List,
    String,
    Struct,
    SymbolField,
    Timestamp,
    UInt32,
    UInt64,
    Union,
)
from babelsdk.api import (
    Api,
    ApiOperation,
)
from babelsdk.babel.parser import (
    BabelAlias,
    BabelInclude,
    BabelNamespace,
    BabelOpDef,
    BabelSymbol,
    BabelTypeDef,
)
from babelsdk.segmentation import (
    Segment,
    SegmentList,
    Segmentation,
)

class TowerOfBabel(object):

    data_types = [
        Binary,
        Boolean,
        Float,
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

    # FIXME: Version should not have a default.
    def __init__(self, paths, version='0.1b1', debug=False):
        """Creates a new tower of babel."""

        self._debug = debug
        self._logger = logging.getLogger('babelsdk.dsl.tower')

        self.api = Api(version=version)

        # A list of all (path, raw text) of API descriptions
        self._scriptures = []
        for path in paths:
            with open(path) as f:
                scripture = f.read()
                self._scriptures.append((path, scripture))

        self.parser = BabelParser(debug=debug)

    def parse(self):
        """Parses each Babel file and returns an API description."""
        for path, scripture in self._scriptures:
            res = self.parse_scripture(scripture)
            if res:
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
            composite_type_obj = Struct
            if item.extends:
                if item.extends not in env:
                    raise Exception('Data type %r is undefined')
                else:
                    super_type = env.get(item.extends)
        elif item.composite_type == 'union':
            composite_type_obj = Union
        else:
            raise ValueError('Unknown composite_type %r'
                             % item.composite_type)
        api_type_fields = []
        for babel_field in item.fields:
            if isinstance(babel_field, BabelSymbol):
                api_type_field = SymbolField(babel_field.name, babel_field.doc)
            elif babel_field.data_type_name not in env:
                raise Exception('Symbol %r is undefined' % babel_field.data_type_name)
            else:
                obj = env[babel_field.data_type_name]
                if inspect.isclass(obj):
                    data_type = obj(**dict(babel_field.data_type_attrs))
                elif babel_field.data_type_attrs:
                    # An instance of a type cannot have any additional
                    # attributes specified.
                    raise Exception('Attributes cannot be specified for instantiated '
                                    'type %r.' % babel_field.data_type_name)
                else:
                    data_type = env[babel_field.data_type_name]

                api_type_field = Field(
                    babel_field.name,
                    data_type,
                    babel_field.doc,
                    nullable=babel_field.nullable,
                )
            api_type_fields.append(api_type_field)
        api_type = composite_type_obj(item.name, item.doc, api_type_fields, super_type)
        for example_label, example in item.examples.items():
            api_type.add_example(example_label, dict(example))
        env[item.name] = api_type
        return api_type

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

        for item in desc[:]:
            if isinstance(item, BabelInclude):
                self._include_babelh(env, os.path.dirname(path), item.target)
            elif isinstance(item, BabelAlias):
                self._create_alias(env, item)
            elif isinstance(item, BabelTypeDef):
                api_type = self._create_type(env, item)
                namespace.add_data_type(api_type)
            elif isinstance(item, BabelOpDef):
                request_segmentation = self._babel_field_to_segments(
                    env,
                    item.request_segmentation,
                )
                response_segmentation = self._babel_field_to_segments(
                    env,
                    item.response_segmentation,
                )
                error_data_type = self._resolve_error_data_type(
                    env,
                    item.error_data_type_name,
                )
                operation = ApiOperation(
                    item.name,
                    item.name,
                    item.doc,
                    request_segmentation,
                    response_segmentation,
                    error_data_type,
                )
                namespace.add_operation(operation)
            else:
                raise Exception('Unknown Babel Declaration Type %r'
                                % item.__class__.__name__)

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

    def _babel_field_to_segments(self, env, fields):
        segments = []
        for field in fields:
            if field.data_type_name == 'SList':
                data_type_name = dict(field.data_type_attrs)['data_type'].name
                segment_cls = SegmentList
            else:
                data_type_name = field.data_type_name
                segment_cls = Segment

            obj = env.get(data_type_name)
            if not obj:
                raise Exception('Symbol %r is undefined' % data_type_name)
            elif inspect.isclass(obj):
                data_type = obj()
            else:
                data_type = obj

            segment = segment_cls(field.name, data_type)
            segments.append(segment)
        return Segmentation(segments)

    def _resolve_error_data_type(self, env, data_type_name):
        if not data_type_name:
            return None

        if data_type_name not in env:
            raise Exception('Symbol %r is undefined' % data_type_name)

        data_type = env.get(data_type_name)
        if not isinstance(data_type, Union):
            raise Exception('%r must be a Union data type' % data_type_name)

        return data_type
