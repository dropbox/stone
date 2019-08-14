
from collections import defaultdict, deque
from stone.ir import(
    Struct,
    StructField,
    Union,
    UserDefined,
)

from proto_type_mapping import map_stone_type_to_proto, is_primitive_data

NESTED_VAL = 2

def get_order_types(namespace):
    struc_map = defaultdict(int)
    for data in namespace.data_types:
        struc_map[data.name] += 1
        if isinstance(data, UserDefined):
            print("yelo", data)
            for field in data.fields:
                if not is_primitive_data(field.data_type):
                    struc_map[field.data_type.name] += 1

    return struc_map
