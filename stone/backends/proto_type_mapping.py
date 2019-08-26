from __future__ import unicode_literals

from stone.ir import (
    is_boolean_type,
    is_bytes_type,
    is_float32_type,
    is_float64_type,
    is_int32_type,
    is_int64_type,
    is_uint32_type,
    is_uint64_type,
    is_string_type,
    is_timestamp_type,
    is_void_type,
    Primitive
)

def map_primitive_type(data_type):

    if is_string_type(data_type):
        return 'string'

    elif is_boolean_type(data_type):
        return 'bool'

    elif is_int32_type(data_type):
        return 'int32'

    elif is_int64_type(data_type):
        return 'int64'

    elif is_uint32_type(data_type):
        return 'uint32'

    elif is_uint64_type(data_type):
        return 'uint64'

    elif is_float32_type(data_type):
        return 'float'

    elif is_float64_type(data_type):
        return 'double'

    elif is_bytes_type(data_type):
        return 'bytes'

    elif is_void_type(data_type):
        return "google.protobuf.Empty"
        
    else:
        raise Exception(
            "This data type is currently not supported."
        )

def is_primitive_data(data_type):
    return isinstance(data_type, Primitive)
