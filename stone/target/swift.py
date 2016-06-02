from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os

from contextlib import contextmanager

from stone.data_type import (
    Boolean,
    Bytes,
    DataType,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    String,
    Timestamp,
    UInt32,
    UInt64,
    Void,
    is_boolean_type,
    is_bytes_type,
    is_list_type,
    is_string_type,
    is_struct_type,
    is_timestamp_type,
    is_union_type,
    is_numeric_type,
    is_nullable_type,
    is_user_defined_type,
    is_void_type,
)
from stone.generator import CodeGenerator
from stone.target.swift_helpers import (
    fmt_class,
    fmt_func,
    fmt_obj,
    fmt_type,
    fmt_var,
)


_serializer_type_table = {
    Boolean: 'Serialization._BoolSerializer',
    Bytes: 'Serialization._NSDataSerializer',
    Float32: 'Serialization._FloatSerializer',
    Float64: 'Serialization._DoubleSerializer',
    Int32: 'Serialization._Int32Serializer',
    Int64: 'Serialization._Int64Serializer',
    List: 'ArraySerializer({})',
    String: 'Serialization._StringSerializer',
    Timestamp: 'NSDateSerializer("{}")',
    UInt32: 'Serialization._UInt32Serializer',
    UInt64: 'Serialization._UInt64Serializer',
    Void: 'Serialization._VoidSerializer',
}


class SwiftBaseGenerator(CodeGenerator):
    """Wrapper class over Babel generator for Swift logic."""
    @contextmanager
    def function_block(self, func, args, return_type=None):
        signature = '{}({})'.format(func, args)
        if return_type:
            signature += ' -> {}'.format(return_type)
        with self.block(signature):
            yield

    def _func_args(self, args_list, newlines=False, force_first=False):
        out = []
        first = True
        for k, v in args_list:
            if first and force_first and '=' not in v:
                k = "{} {}".format(k, k)
            if v is not None:
                out.append('{}: {}'.format(k, v))
            first = False
        sep = ', '
        if newlines:
            sep += '\n' + self.make_indent()
        return sep.join(out)

    @contextmanager
    def class_block(self, thing, protocols=None):
        protocols = protocols or []
        extensions = []

        if isinstance(thing, DataType):
            name = fmt_class(thing.name)
            if thing.parent_type:
                extensions.append(self.fmt_complex_type(thing.parent_type))
        else:
            name = thing
        extensions.extend(protocols)

        extend_suffix = ': {}'.format(', '.join(extensions)) if extensions else ''

        with self.block('public class {}{}'.format(name, extend_suffix)):
            yield

    def _docf(self, tag, val):
        if tag == 'route':
            return fmt_func(val)
        elif tag == 'field':
            if '.' in val:
                cls, field = val.split('.')
                return ('{} in {}'.format(fmt_var(field),
                        fmt_class(cls)))
            else:
                return fmt_var(val)
        elif tag in ('type', 'val', 'link'):
            return val
        else:
            import pdb
            pdb.set_trace()
            return val

    def _struct_init_args(self, data_type, namespace=None):
        args = []
        for field in data_type.all_fields:
            name = fmt_var(field.name)
            value = self.fmt_complex_type(field.data_type)
            field_type = field.data_type
            if is_nullable_type(field_type):
                field_type = field_type.data_type
                nullable = True
            else:
                nullable = False

            if field.has_default:
                if is_union_type(field_type):
                    default = '.{}'.format(fmt_class(field.default.tag_name))
                else:
                    default = fmt_obj(field.default)
                value += ' = {}'.format(default)
            elif nullable:
                value += ' = nil'
            arg = (name, value)
            args.append(arg)
        return args

    def fmt_complex_type(self, data_type, serializer=False):
        suffix = 'Serializer' if serializer else ''
        if is_nullable_type(data_type):
            data_type = data_type.data_type
            nullable = True
        else:
            nullable = False
        if is_list_type(data_type):
            ret = 'Array{}<{}>'.format(
                suffix,
                self.fmt_complex_type(data_type.data_type, serializer)
            )
            suffix = ''
        elif is_user_defined_type(data_type):
            ret = '{}.{}'.format(fmt_class(data_type.namespace.name),
                                 fmt_class(data_type.name))
        else:
            ret = fmt_type(data_type)

        ret += suffix
        if nullable:
            if serializer:
                ret = 'NullableSerializer<{}>'.format(ret)
            else:
                ret += '?'

        return ret

    def fmt_serial_type(self, data_type):
        return _serializer_type_table.get(data_type.__class__, fmt_class(data_type.name))

    def _serializer_obj(self, data_type):
        if is_nullable_type(data_type):
            data_type = data_type.data_type
            nullable = True
        else:
            nullable = False


        if is_user_defined_type(data_type):
            ret = "{}.{}Serializer()".format(fmt_class(data_type.namespace.name),
                                             fmt_class(data_type.name))
        else:
            ret = self.fmt_serial_type(data_type)

        if is_list_type(data_type):
            ret = ret.format(
                self._serializer_obj(data_type.data_type))
        elif is_timestamp_type(data_type):
            ret = ret.format(data_type.format)
        if nullable:
            ret = 'NullableSerializer({})'.format(ret)

        return ret
