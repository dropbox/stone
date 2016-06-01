from __future__ import absolute_import, division, print_function, unicode_literals

import json
import six

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
)
from stone.target.helpers import (
    fmt_camel,
)

_type_table = {
    Boolean: 'Boolean',
    Bytes: 'String',
    Float32: 'Number',
    Float64: 'Number',
    Int32: 'Number',
    Int64: 'Number',
    List: 'Array',
    String: 'String',
    UInt32: 'Number',
    UInt64: 'Number',
    Timestamp: 'Object',
    Void: 'null',
}


def fmt_obj(o):
    if isinstance(o, six.text_type):
        # Prioritize single-quoted strings per JS style guides.
        return repr(o).lstrip('u')
    else:
        return json.dumps(o, indent=2)


def fmt_type(data_type):
    return _type_table.get(data_type.__class__, 'Object')


def fmt_func(name):
    return fmt_camel(name)


def fmt_var(name):
    return fmt_camel(name)
