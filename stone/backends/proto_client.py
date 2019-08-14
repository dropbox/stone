from stone.backend import CodeBackend
from stone.ir import(
    Struct,
    StructField,
)
from proto_type_mapping import map_stone_type_to_proto, is_primitive_data
from proto_helpers import(
    get_order_types,
    NESTED_VAL,
)

class ProtoBackend(CodeBackend):
    def generate(self, api):
        with self.output_to_relative_path('test.proto'):
            for namespace in api.namespaces.values():

                self._create_package(namespace.name)
                self._generate_types(namespace)

    def _create_package(self, val):
        self.emit(self._expr_st("package", val))
        self.emit()

    def _generate_types(self, namespace):

        for data in namespace.data_types:
            print(data)
            self._create_proto_data(data)

    def _create_proto_data(self, data):
        if isinstance(data, Struct):
            self._generate_messages(data)

    def _generate_messages(self, data):

        self.emit(self._obj_start("message " + data.name))

        counter = 0
        with self.indent():
            for field in data.fields:
                #check if nested userdefined dataytpe
                if not is_primitive_data(field.data_type):
                    typ = field.data_type.name

                else:
                    typ = map_stone_type_to_proto(field.data_type)
                self.emit(self._expr_eq(typ, field.name, str(counter)))
                counter += 1

        self.emit(self._obj_end())
        self.emit()


    def _generate_message_cont(self, msg):
        pass

    DATA_TYPE_GENERATOR_MAP = {
        'struct': _generate_messages,
        #union_inside
        #union_outside
    }

    #FORMAT STRINGS
    def _obj_start(self, s):
        return (u'{} {}'.format(s, u'{'))
    def _obj_end(self):
        return (u'}')

    def _expr_eq(self, typ, name, value):
        return (u'{}\t{} = {};'.format(typ, name, value))
    def _expr_st(self, typ, name):
        return (u'{} {};'.format(typ, name))
