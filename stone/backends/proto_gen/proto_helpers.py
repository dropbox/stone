
from collections import defaultdict, deque
from stone.ir import(
    Struct,
    StructField,
    Union,
    UserDefined,
)

from proto_type_mapping import map_stone_type_to_proto, is_primitive_data

def get_order_structs(namespace):
    struc_map = defaultdict(int)
    for data in namespace.data_types:
        if data.name not in struc_map:
            struc_map[data.name] += 1
        if isinstance(data, UserDefined):
            for field in data.fields:
                if not is_primitive_data(field.data_type):
                    print(field.name)
                    struc_map[field.data_type.name] += 1

    for k,v in struc_map.items():
        print(k,v)
