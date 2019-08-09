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
    # is_float_type,
    # is_integer_type,
    is_float32_type,
    is_float64_type,
    is_int32_type,
    is_int64_type,
    # is_list_type,
    # is_map_type,
    # is_nullable_type,
    is_string_type,
    is_timestamp_type,
    # is_user_defined_type,
    # is_void_type,
)

def map_stone_type_to_proto(data_type):

    if is_string_type(data_type):
        return 'string'

    elif is_boolean_type(data_type):
        return 'bool'

    elif is_int32_type(data_type):
        return 'int32'

    elif is_int64_type(data_type):
        return 'int64'

    elif is_float32_type(data_type):
        return 'float32'

    elif is_float64_type(data_type):
        return 'float64'

    elif is_bytes_type(data_type):
        return 'bytes'

    elif is_timestamp_type(data_type):
        return 'timestamp'