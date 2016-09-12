from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import json
import os
import re

from contextlib import contextmanager

from stone.data_type import (
    Int32,
    Int64,
    UInt32,
    UInt64,
    is_boolean_type,
    is_float_type,
    is_list_type,
    is_numeric_type,
    is_string_type,
    is_struct_type,
    is_timestamp_type,
    is_user_defined_type,
    is_union_type,
    is_void_type,
    unwrap_nullable,
)
from stone.target.obj_c_helpers import (
    fmt_alloc_call,
    fmt_camel,
    fmt_camel_upper,
    fmt_class,
    fmt_class_prefix,
    fmt_func,
    fmt_func_args,
    fmt_func_args_declaration,
    fmt_func_call,
    fmt_import,
    fmt_property_str,
    fmt_public_name,
    fmt_serial_obj,
    fmt_signature,
    fmt_type,
    fmt_var,
    is_primitive_type,
    is_ptr_type,
)
from stone.target.obj_c import (
    base,
    comment_prefix,
    ObjCBaseGenerator,
    stone_warning,
    undocumented,
)

_cmdline_parser = argparse.ArgumentParser(
    prog='ObjC-test-generator',
    description=(
        'Generates unit tests for the Obj C SDK.'),
)


class ObjCTestGenerator(ObjCBaseGenerator):
    """Generates Xcode tests for Objective C SDK."""
    cmdline_parser = _cmdline_parser

    def generate(self, api):
        with self.output_to_relative_path('DbxSerializationTests.m'):
            self.emit_raw(base)
            self.emit('#import <XCTest/XCTest.h>')
            self.emit()
            self._generate_testing_imports(api)

            with self.block_h('DbxSerializationTests', extensions=['XCTestCase']):
                pass

            self.emit()
            self.emit()

            with self.block_m('DbxSerializationTests'):

                with self.block_func(func='checkError',
                                     args=fmt_func_args_declaration([('originalObj', 'id'), ('outputObj', 'id')])):
                    msg = "\\nSerialization and deserialization failed to preserve object data:\\n\\nBefore:\\n %@ \\n\\nAfter:\\n %@.\\n\\n"
                    self.emit('NSAssert(([[originalObj description] isEqual:[outputObj description]]), @"{}", originalObj, outputObj);'.format(msg))
                for namespace in api.namespaces.values():
                    self._generate_namespace_tests(namespace)

    def _generate_namespace_tests(self, namespace):
        ns_name = fmt_public_name(namespace.name)

        self.emit()
        self.emit('/// Serialization tests for the {} namespace.'.format(ns_name))
        self.emit()
        self.emit()
        for data_type in namespace.linearize_data_types():
            class_name = fmt_public_name(data_type.name)
            if is_user_defined_type(data_type):
                examples = data_type.get_examples()
                for example_type in examples:
                    test_name = 'testSerialize{}{}{}'.format(ns_name,
                                                             class_name,
                                                             fmt_camel_upper(example_type, reserved=False))
                    with self.block_func(func=test_name,
                                         args=[]):
                        self.emit('/// Data from the "{}" example'.format(example_type))
                        example_data = examples[example_type].value
                        result_args = []

                        for field in data_type.all_fields:
                            if field.name in example_data:
                                result_args += self._get_example_data(example_data[field.name], field)
                            else:
                                if not is_void_type(field.data_type):
                                    result_args.append((fmt_var(field.name), self._fmt_default(field.data_type)))

                        args_str = fmt_func_args(result_args)

                        if '\n' not in args_str:
                            if is_struct_type(data_type) and data_type.has_enumerated_subtypes():
                                for tags, subtype in data_type.get_all_subtypes_with_tags():
                                    assert len(tags) == 1, tags
                                    tag = tags[0]
                                    if tag == example_data['.tag']:
                                        self.emit('{} *obj = {};'.format(fmt_class_prefix(subtype), self._get_example_data(example_data, subtype)))
                                        self.emit('NSData *serializedData = [DropboxTransportClient jsonDataWithDictionary:[{} serialize:obj]];'.format(fmt_class_prefix(subtype)))
                                        self.emit('id jsonObj = [NSJSONSerialization JSONObjectWithData:serializedData options:NSJSONReadingMutableContainers error:nil];')
                                        self.emit('{} *outputObj = [{} deserialize:jsonObj];'.format(fmt_class_prefix(subtype), fmt_class_prefix(subtype)))
                                        self.emit('[self checkError:obj outputObj:outputObj];')
                            else:   
                                self.emit('{} *obj = {};'.format(fmt_class_prefix(data_type), fmt_func_call(fmt_alloc_call(fmt_class_prefix(data_type)), self._cstor_name_from_fields_names(result_args), args_str)))
                                self.emit('NSData *serializedData = [DropboxTransportClient jsonDataWithDictionary:[{} serialize:obj]];'.format(fmt_class_prefix(data_type)))
                                self.emit('id jsonObj = [NSJSONSerialization JSONObjectWithData:serializedData options:NSJSONReadingMutableContainers error:nil];')
                                self.emit('{} *outputObj = [{} deserialize:jsonObj];'.format(fmt_class_prefix(data_type), fmt_class_prefix(data_type)))
                                self.emit('[self checkError:obj outputObj:outputObj];')
                    self.emit()

    def _get_example_data(self, example_value, field):    
        data_type, nullable = unwrap_nullable(field.data_type)
        field_name = fmt_var(field.name)

        result_args = []

        if is_user_defined_type(data_type):
            obj_args = []

            if is_union_type(data_type):
                for field in data_type.all_fields:
                    if field.name == example_value['.tag']:
                        if not is_void_type(field.data_type):
                            if field.name in example_value:
                                self._get_example_data(example_value[field.name], field)
                            else:
                                self._get_example_data(example_value, field)
                            obj_args.append((fmt_var(field.name), fmt_var(field.name)))

                field_value = fmt_func_call(caller=fmt_alloc_call(fmt_class_prefix(data_type)),
                                       callee='initWith{}'.format(fmt_camel_upper(example_value['.tag'])),
                                       args=fmt_func_args(obj_args))
                self.emit('{} *{} = {};'.format(fmt_class_prefix(data_type),
                    field_name, field_value))
            else:
                if data_type.has_enumerated_subtypes():
                    for tags, subtype in data_type.get_all_subtypes_with_tags():
                        assert len(tags) == 1, tags
                        tag = tags[0]
                        if tag == example_value['.tag']:
                            self._get_example_data(example_value, subtype)
                else:
                    for field in data_type.all_fields:
                        if field.name in example_value:
                            obj_args.append((fmt_var(field.name), self._get_example_data(example_value[field.name], field.data_type)))
                        else:
                            if not is_void_type(field.data_type):
                                obj_args.append((fmt_var(field.name), self._fmt_default(field.data_type)))
                    field_value = fmt_func_call(fmt_alloc_call(fmt_class_prefix(data_type)),
                        'initWith{}'.format(fmt_camel_upper(data_type.all_fields[0].name)), fmt_func_args(obj_args))
            
                    self.emit('{} *{} = {};'.format(fmt_class_prefix(data_type),
                        field_name, field_value))

            result_args.append((field_name, field_name))
        elif is_list_type(data_type):
            if example_value:
                field_value = '@[{}]'.format(self._get_example_data(example_value[0], field))
            else:
                field_value = 'nil'
            self.emit('NSArray *{} = {};'.format(field_name, field_value))
            result_args.append((field_name, field_name))
        elif is_numeric_type(data_type):
            if is_float_type(data_type):
                field_value = '[NSNumber numberWithDouble:{}]'.format(example_value)
            elif isinstance(data_type, (UInt64, Int64)):
                field_value = '[NSNumber numberWithLong:{}]'.format(example_value)
            else:
                field_value = '[NSNumber numberWithInt:{}]'.format(example_value)
            result_args.append((field_name, field_value))
        elif is_timestamp_type(data_type):
            field_value = '[DbxNSDateSerializer deserialize:@"{}" dateFormat:@"{}"]'.format(example_value, data_type.format)
            self.emit('NSDate *{} = {};'.format(field_name, field_value))
            result_args.append((field_name, field_name))
        elif is_string_type(data_type):
            field_value = '@"{}"'.format(example_value)
            result_args.append((field_name, field_value))
        elif is_boolean_type(data_type):
            field_value = '@YES' if bool(example_value) else '@NO'
            result_args.append((field_name, field_value))

        return result_args

    def _fmt_default(self, data_type):
        data_type, nullable = unwrap_nullable(data_type)

        result = 'DEFAULT'

        if nullable:
            return 'nil'

        if is_user_defined_type(data_type):
            result = fmt_func_call(fmt_alloc_call(fmt_class_prefix(data_type)), 'init', [])
        elif is_list_type(data_type):
            result = fmt_func_call(fmt_alloc_call('NSArray'), 'init', [])
        elif is_numeric_type(data_type):
            if is_float_type(data_type):
                result = '[NSNumber numberWithDouble:5]'
            else:
                result = '[NSNumber numberWithInt:5]'
        elif is_timestamp_type(data_type):
            result = '[[NSDateFormatter new] setDateFormat:[self convertFormat:@"test"]]'
        elif is_string_type(data_type):
            result = '@"teststring"'
        elif is_boolean_type(data_type):
            result = '@YES'

        return result

    def _generate_testing_imports(self, api):
        import_classes = ['DbxStoneSerializers', 'DropboxTransportClient']
        for namespace in api.namespaces.values():
            for data_type in namespace.linearize_data_types():
                import_classes.append(fmt_class_prefix(data_type))
        self._generate_imports_m(import_classes)
