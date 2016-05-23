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
)
from stone.target.helpers import (
    fmt_pascal,
    fmt_underscores,
)

_type_table = {
    Boolean: 'bool',
    Bytes: 'bytes',
    Float32: 'float',
    Float64: 'float',
    Int32: 'int',
    Int64: 'long',
    List: 'list',
    String: 'str',
    Timestamp: 'datetime',
    UInt32: 'long',
    UInt64: 'long',
}

_reserved_keywords = {
    'break',
    'class',
    'continue',
    'for',
    'pass',
    'while',
}


def _rename_if_reserved(s):
    if s in _reserved_keywords:
        return s + '_'
    else:
        return s


def fmt_class(name, check_reserved=False):
    s = fmt_pascal(name)
    return _rename_if_reserved(s) if check_reserved else s


def fmt_func(name, check_reserved=False):
    s = fmt_underscores(name)
    return _rename_if_reserved(s) if check_reserved else s


def fmt_obj(o):
    return pprint.pformat(o, width=1)


def fmt_type(data_type):
    return _type_table.get(data_type.__class__, fmt_class(data_type.name))


def fmt_var(name, check_reserved=False):
    s = fmt_underscores(name)
    return _rename_if_reserved(s) if check_reserved else s
