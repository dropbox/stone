from stone.ir import (
    # Alias,
    # ApiNamespace,
    # DataType,
    # List,
    # Map,
    # Nullable,
    Timestamp,
    # UserDefined,
    # is_alias,
    is_boolean_type,
    is_bytes_type,
    is_float32_type,
    is_float64_type,
    is_int32_type,
    is_int64_type,
    is_uint32_type,
    is_uint64_type,
    # is_list_type,
    # is_map_type,
    # is_nullable_type,
    is_string_type,
    is_timestamp_type,
    # is_user_defined_type,
    # is_void_type,
    Primitive
)

def map_stone_type_to_proto(data_type):

    if is_string_type(data_type):
        return u'string'

    elif is_boolean_type(data_type):
        return u'bool'

    elif is_int32_type(data_type):
        return u'int32'

    elif is_int64_type(data_type):
        return u'int64'

    elif is_uint32_type(data_type):
        return 'uint32'

    elif is_uint64_type(data_type):
         return 'uint64'

    elif is_float32_type(data_type):
        return u'float'

    elif is_float64_type(data_type):
        return u'double'

    elif is_bytes_type(data_type):
        return 'bytes'

    elif is_timestamp_type(data_type):
        return 'timestamp'
    else:
        return None

def is_primitive_data(data_type):
    return isinstance(data_type, Primitive)
