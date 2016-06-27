from __future__ import absolute_import, division, print_function, unicode_literals

import pprint

from stone.data_type import (
    Boolean,
    Bytes,
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
    is_list_type,
    is_user_defined_type,
    unwrap_nullable,
)
from .helpers import split_words

# This file defines *stylistic* choices for Swift
# (ie, that class names are UpperCamelCase and that variables are lowerCamelCase)


_type_table = {
    Boolean: 'Bool',
    Bytes: 'NSData',
    Float32: 'Float',
    Float64: 'Double',
    Int32: 'Int32',
    Int64: 'Int64',
    List: 'Array',
    String: 'String',
    Timestamp: 'NSDate',
    UInt32: 'UInt32',
    UInt64: 'UInt64',
    Void: 'Void',
}

_reserved_words = {
    'description',
    'bool',
    'nsdata'
    'float',
    'double',
    'int32',
    'int64',
    'list',
    'string',
    'timestamp',
    'uint32',
    'uint64',
    'void',
    'associatedtype',
    'class',
    'deinit',
    'enum',
    'extension',
    'func',
    'import',
    'init',
    'inout',
    'internal',
    'let',
    'operator',
    'private',
    'protocol',
    'public',
    'static',
    'struct',
    'subscript',
    'typealias',
    'var',
}


def fmt_obj(o):
    assert not isinstance(o, dict), "Only use for base type literals"
    if o is True:
        return 'true'
    if o is False:
        return 'false'
    if o is None:
        return 'nil'
    return pprint.pformat(o, width=1)


def _format_camelcase(name, lower_first=True):
    words = [word.capitalize() for word in split_words(name)]
    if lower_first:
        words[0] = words[0].lower()
    ret = ''.join(words)
    if ret.lower() in _reserved_words:
        ret += '_'
    return ret


def fmt_class(name):
    return _format_camelcase(name, lower_first=False)


def fmt_func(name):
    return _format_camelcase(name)


def fmt_type(data_type):
    data_type, nullable = unwrap_nullable(data_type)

    if is_user_defined_type(data_type):
        result = '{}.{}'.format(fmt_class(data_type.namespace.name),
                                fmt_class(data_type.name))
    else:
        result = _type_table.get(data_type.__class__, fmt_class(data_type.name))
        
        if is_list_type(data_type):
            result = result + '<{}>'.format(fmt_type(data_type.data_type))            
    
    return result if not nullable else result + '?'


def fmt_var(name):
    return _format_camelcase(name)
