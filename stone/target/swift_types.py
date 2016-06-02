from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import json
import os
import shutil

from contextlib import contextmanager

from stone.data_type import (
    is_list_type,
    is_nullable_type,
    is_numeric_type,
    is_string_type,
    is_struct_type,
    is_union_type,
    is_void_type,
)
from stone.target.swift_helpers import (
    fmt_class,
    fmt_func,
    fmt_var,
)
from stone.target.swift import SwiftBaseGenerator

auto_generated_warning = '/* Auto-generated by Stone, do not modify. */'

# This will be at the top of the generated file.
base = """\
{}
import Foundation
""".format(auto_generated_warning)

_cmdline_parser = argparse.ArgumentParser(prog='swift-types-generator')
_cmdline_parser.add_argument(
    '-r',
    '--route-method',
    help=('A string used to construct the location of a Swift method for a '
          'given route; use {ns} as a placeholder for namespace name and '
          '{route} for the route name.'),
)
_cmdline_parser.add_argument(
    '-a',
    '--attribute',
    action='append',
    type=str,
    default=[],
    help='Route attribute to include in the generated code.',
)


class SwiftTypesGenerator(SwiftBaseGenerator):
    """Generates Swift modules to represent the input Stone spec."""
    cmdline_parser = _cmdline_parser
    def generate(self, api):
        rsrc_folder = os.path.join(os.path.dirname(__file__), 'swift_rsrc')
        self.logger.info('Copying StoneValidators.swift to output folder')
        shutil.copy(os.path.join(rsrc_folder, 'StoneValidators.swift'),
                    self.target_folder_path)
        self.logger.info('Copying StoneSerializers.swift to output folder')
        shutil.copy(os.path.join(rsrc_folder, 'StoneSerializers.swift'),
                    self.target_folder_path)
        self.logger.info('Copying StoneBase.swift to output folder')
        shutil.copy(os.path.join(rsrc_folder, 'StoneBase.swift'),
                    self.target_folder_path)

        jazzy_cfg_path = os.path.join(rsrc_folder, 'jazzy.json')
        with open(jazzy_cfg_path) as jazzy_file:
            jazzy_cfg = json.load(jazzy_file)

        for namespace in api.namespaces.values():
            ns_class = fmt_class(namespace.name)
            with self.output_to_relative_path('{}.swift'.format(ns_class)):
                self._generate_base_namespace_module(namespace)
            jazzy_cfg['custom_categories'][1]['children'].append(ns_class)

            if namespace.routes:
                jazzy_cfg['custom_categories'][0]['children'].append(ns_class + 'Routes')

        with self.output_to_relative_path('../.jazzy.json'):
            self.emit_raw(json.dumps(jazzy_cfg, indent=2)+'\n')

    def _generate_base_namespace_module(self, namespace):
        self.emit_raw(base)

        self.emit('/**')
        self.emit('    Datatypes and serializers for the {} namespace'.format(namespace.name))
        self.emit('*/')
        with self.block('public class {}'.format(fmt_class(namespace.name))):
            for data_type in namespace.linearize_data_types():
                if is_struct_type(data_type):
                    self._generate_struct_class(namespace, data_type)
                elif is_union_type(data_type):
                    self._generate_union_type(namespace, data_type)
            if namespace.routes:
                self._generate_route_objects(namespace)

    def _determine_validator_type(self, data_type):
        if is_nullable_type(data_type):
            data_type = data_type.data_type
            nullable = True
        else:
            nullable = False
        if is_list_type(data_type):
            item_validator = self._determine_validator_type(data_type.data_type)
            if item_validator:
                v = "arrayValidator({})".format(
                    self._func_args([
                        ("minItems", data_type.min_items),
                        ("maxItems", data_type.max_items),
                        ("itemValidator", item_validator),
                    ])
                )
            else:
                return None
        elif is_numeric_type(data_type):
            v = "comparableValidator({})".format(
                self._func_args([
                    ("minValue", data_type.min_value),
                    ("maxValue", data_type.max_value),
                ])
            )
        elif is_string_type(data_type):
            pat = data_type.pattern if data_type.pattern else None
            pat = pat.encode('unicode_escape').replace("\"", "\\\"") if pat else pat                
            v = "stringValidator({})".format(
                self._func_args([
                    ("minLength", data_type.min_length),
                    ("maxLength", data_type.max_length),
                    ("pattern", '"{}"'.format(pat) if pat else None),
                ])
            )
        else:
            return None

        if nullable:
            v = "nullableValidator({})".format(v)
        return v

    def _generate_struct_class(self, namespace, data_type):
        self.emit('/**')
        if data_type.doc:
            doc = self.process_doc(data_type.doc, self._docf)
        else:
            doc = 'The {} struct'.format(fmt_class(data_type.name))
        self.emit_wrapped_text(doc, prefix='    ', width=120)
        self.emit('*/')
        protocols = []
        if not data_type.parent_type:
            protocols.append('CustomStringConvertible')

        with self.class_block(data_type, protocols=protocols):
            for field in data_type.fields:
                fdoc = self.process_doc(field.doc, self._docf) if field.doc else 'Undocumented'
                self.emit_wrapped_text(fdoc, prefix='/// ', width=120)
                self.emit('public let {}: {}'.format(
                    fmt_var(field.name),
                    self.fmt_complex_type(field.data_type),
                ))
            self._generate_struct_init(namespace, data_type)

            decl = 'public var' if not data_type.parent_type else 'public override var'

            with self.block('{} description: String'.format(decl)):
                cls = fmt_class(data_type.name)+'Serializer'
                self.emit('return "\(SerializeUtil.prepareJSONForSerialization' +
                          '({}().serialize(self)))"'.format(cls))

        self._generate_struct_class_serializer(namespace, data_type)

    def _generate_struct_init(self, namespace, data_type):
        # init method
        args = self._struct_init_args(data_type)
        if data_type.parent_type and not data_type.fields:
            return
        with self.function_block('public init', self._func_args(args)):
            for field in data_type.fields:
                v = fmt_var(field.name)
                validator = self._determine_validator_type(field.data_type)
                if validator:
                    self.emit('{}(value: {})'.format(validator, v))
                self.emit('self.{} = {}'.format(v, v))
            if data_type.parent_type:
                func_args = [(fmt_var(f.name),
                              fmt_var(f.name))
                             for f in data_type.parent_type.all_fields]
                self.emit('super.init({})'.format(self._func_args(func_args)))

    def _generate_enumerated_subtype_serializer(self, namespace, data_type):
        with self.block('switch value'):
            for tags, subtype in data_type.get_all_subtypes_with_tags():
                assert len(tags) == 1, tags
                tag = tags[0]
                tagvar = fmt_var(tag)
                self.emit('case let {} as {}:'.format(
                    tagvar,
                    self.fmt_complex_type(subtype)
                ))

                with self.indent():
                    with self.block('for (k,v) in Serialization.getFields({}.serialize({}))'.format(
                        self._serializer_obj(subtype), tagvar
                    )):
                        self.emit('output[k] = v')
                    self.emit('output[".tag"] = .Str("{}")'.format(tag))
            self.emit('default: fatalError("Tried to serialize unexpected subtype")')

    def _generate_struct_base_class_deserializer(self, namespace, data_type):
            args = []
            for field in data_type.all_fields:
                var = fmt_var(field.name)
                self.emit('let {} = {}.deserialize(dict["{}"] ?? .Null)'.format(
                    var,
                    self._serializer_obj(field.data_type),
                    field.name,
                ))

                args.append((var, var))
            self.emit('return {}({})'.format(
                fmt_class(data_type.name),
                self._func_args(args)
            ))

    def _generate_enumerated_subtype_deserializer(self, namespace, data_type):
        self.emit('let tag = Serialization.getTag(dict)')
        with self.block('switch tag'):
            for tags, subtype in data_type.get_all_subtypes_with_tags():
                assert len(tags) == 1, tags
                tag = tags[0]
                self.emit('case "{}":'.format(tag))
                with self.indent():
                    self.emit('return {}.deserialize(json)'.format(self._serializer_obj(subtype)))
            self.emit('default:')
            with self.indent():
                if data_type.is_catch_all():
                    self._generate_struct_base_class_deserializer(namespace, data_type)
                else:
                    self.emit('fatalError("Unknown tag \\(tag)")')

    def _generate_struct_class_serializer(self, namespace, data_type):
        with self.serializer_block(data_type):
            with self.serializer_func(data_type):
                if not data_type.all_fields:
                    self.emit('let output = [String: JSON]()')
                else:
                    intro = 'var' if data_type.has_enumerated_subtypes() else 'let'
                    self.emit("{} output = [ ".format(intro))
                    for field in data_type.all_fields:
                        self.emit('"{}": {}.serialize(value.{}),'.format(
                            field.name,
                            self._serializer_obj(field.data_type),
                            fmt_var(field.name)
                        ))
                    self.emit(']')

                    if data_type.has_enumerated_subtypes():
                        self._generate_enumerated_subtype_serializer(namespace, data_type)
                self.emit('return .Dictionary(output)')
            with self.deserializer_func(data_type):
                with self.block("switch json"):
                    self.emit("case .Dictionary(let dict):")
                    with self.indent():
                        if data_type.has_enumerated_subtypes():
                            self._generate_enumerated_subtype_deserializer(namespace, data_type)
                        else:
                            self._generate_struct_base_class_deserializer(namespace, data_type)
                    self.emit("default:")
                    with self.indent():
                        self.emit('fatalError("Type error deserializing")')

    def _format_tag_type(self, namespace, data_type):
        if is_void_type(data_type):
            return ''
        else:
            return '({})'.format(self.fmt_complex_type(data_type))

    def _generate_union_type(self, namespace, data_type):
        self.emit('/**')
        if data_type.doc:
            doc = self.process_doc(data_type.doc, self._docf)
        else:
            doc = 'The {} union'.format(fmt_class(data_type.name))
        self.emit_wrapped_text(doc, prefix='    ', width=120)
        self.emit('*/')

        class_type = fmt_class(data_type.name)
        with self.block('public enum {}: CustomStringConvertible'.format(class_type)):
            for field in data_type.all_fields:
                typ = self._format_tag_type(namespace, field.data_type)
                if field.doc:
                    self.emit('/**')
                    self.emit_wrapped_text(self.process_doc(field.doc, self._docf),
                                           prefix='    ', width=120)
                    self.emit('*/')
                self.emit('case {}{}'.format(fmt_class(field.name),
                                                  typ))
            with self.block('public var description: String'):
                cls = class_type+'Serializer'
                self.emit('return "\(SerializeUtil.prepareJSONForSerialization' +
                          '({}().serialize(self)))"'.format(cls))

        self._generate_union_serializer(data_type)

    def _tag_type(self, data_type, field):
        return "{}.{}".format(
            fmt_class(data_type.name),
            fmt_class(field.name)
        )

    def _generate_union_serializer(self, data_type):
        with self.serializer_block(data_type):
            with self.serializer_func(data_type), self.block('switch value'):
                for field in data_type.all_fields:
                    field_type = field.data_type
                    case = '.{}{}'.format(fmt_class(field.name),
                                         '' if is_void_type(field_type) else '(let arg)')
                    self.emit('case {}:'.format(case))

                    with self.indent():
                        if is_void_type(field_type):
                            self.emit('var d = [String: JSON]()')
                        elif (is_struct_type(field_type) and
                                not field_type.has_enumerated_subtypes()):
                            self.emit('var d = Serialization.getFields({}.serialize(arg))'.format(
                                self._serializer_obj(field_type)))
                        else:
                            self.emit('var d = ["{}": {}.serialize(arg)]'.format(
                                field.name,
                                self._serializer_obj(field_type)))
                        self.emit('d[".tag"] = .Str("{}")'.format(field.name))
                        self.emit('return .Dictionary(d)')
            with self.deserializer_func(data_type):
                with self.block("switch json"):
                    self.emit("case .Dictionary(let d):")
                    with self.indent():
                        self.emit('let tag = Serialization.getTag(d)')
                        with self.block('switch tag'):
                            for field in data_type.all_fields:
                                field_type = field.data_type
                                self.emit('case "{}":'.format(field.name))

                                tag_type = self._tag_type(data_type, field)
                                with self.indent():
                                    if is_void_type(field_type):
                                        self.emit('return {}'.format(tag_type))
                                    else:
                                        if (is_struct_type(field_type) and
                                                not field_type.has_enumerated_subtypes()):
                                            subdict = 'json'
                                        else:
                                            subdict = 'd["{}"] ?? .Null'.format(field.name)

                                        self.emit('let v = {}.deserialize({})'.format(
                                            self._serializer_obj(field_type), subdict
                                        ))
                                        self.emit('return {}(v)'.format(tag_type))
                            self.emit('default:')
                            with self.indent():
                                if data_type.catch_all_field:
                                    self.emit('return {}'.format(
                                        self._tag_type(data_type, data_type.catch_all_field)
                                    ))
                                else:
                                    self.emit('fatalError("Unknown tag \(tag)")')
                    self.emit("default:")
                    with self.indent():

                        self.emit('fatalError("Failed to deserialize")')

    def _generate_route_objects(self, namespace):
        self.emit()
        self.emit('// Stone Route Objects')
        self.emit()
        for route in namespace.routes:
            var_name = fmt_func(route.name)
            with self.block('static let {} = Route('.format(var_name),
                            delim=(None, None), after=')'):
                self.emit('name: \"{}\",'.format(route.name))
                self.emit('namespace: \"{}\",'.format(namespace.name))
                self.emit('deprecated: {},'.format('true' if route.deprecated
                                                   is not None else 'false'))
                attrs = []
                for attr_key in self.args.attribute:
                    attr_val = ("\"{}\"".format(route.attrs.get(attr_key))
                            if route.attrs.get(attr_key) else 'nil')
                    attrs.append('\"{}\": {}'.format(attr_key, attr_val))

                self.generate_multiline_list(
                    attrs, delim=('attrs: [', ']'), compact=True)

    @contextmanager
    def serializer_block(self, data_type):
        with self.class_block(fmt_class(data_type.name)+'Serializer',
                              protocols=['JSONSerializer']):
            self.emit("public init() { }")
            yield

    @contextmanager
    def serializer_func(self, data_type):
        with self.function_block('public func serialize',
                                 args=self._func_args([('value', fmt_class(data_type.name))]),
                                 return_type='JSON'):
            yield

    @contextmanager
    def deserializer_func(self, data_type):
        with self.function_block('public func deserialize',
                                 args=self._func_args([('json', 'JSON')]),
                                 return_type=fmt_class(data_type.name)):
            yield