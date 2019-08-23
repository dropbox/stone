from __future__ import unicode_literals
from collections import defaultdict
from stone.ir import(
    Struct,
    StructField,
    Union,
    UserDefined,
)

from stone.backends.proto_type_mapping import is_primitive_data

#FORMAT STRINGS
def _obj_start(s):
    return ('{} {{'.format(s))

def obj_end():
    return ('}')

def expr_eq(typ, name, value):
    return ('{} {}\t= {};'.format(typ, name, value))
def expr_st(typ, name):
    return ('{} {};'.format(typ, name))

def message_fmt(name):
    return _obj_start('message ' + name)
