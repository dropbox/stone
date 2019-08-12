from stone.backend import CodeBackend
from stone.ir import(
    Struct,
    StructField,
)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from proto_type_mapping import map_stone_type_to_proto, is_primitive_data
=======
>>>>>>> Mapping for basic data types
=======
from proto_type_mapping import map_stone_type_to_proto
>>>>>>> Basic Message expression
=======
from proto_type_mapping import map_stone_type_to_proto, is_primitive_data
>>>>>>> Added nesting

class ProtoBackend(CodeBackend):
    def generate(self, api):
        with self.output_to_relative_path('test.proto'):
            for namespace in api.namespaces.values():
                self._create_package(namespace.name)
                self._generate_messages(namespace)

    def _create_package(self, val):
<<<<<<< HEAD
<<<<<<< HEAD
        self.emit(self._expr_st("package", val))
=======
        self.emit("package " + val + ";")
>>>>>>> Mapping for basic data types
=======
        self.emit(self._expr_st("package", val))
>>>>>>> Added nesting
        self.emit()

    def _generate_messages(self, namespace):
        for data in namespace.data_types:
<<<<<<< HEAD
<<<<<<< HEAD
            print(data)
            if isinstance(data, Struct):
                self.emit(self._obj_start("message " + data.name))
                self._generate_message_cont(data)
                self.emit(self._obj_end())
                self.emit()


    def _generate_message_cont(self, msg):
        counter = 0
        with self.indent():
            for field in msg.fields:
                typ = map_stone_type_to_proto(field.data_type) if is_primitive_data(field.data_type) else field.data_type.name
                self.emit(self._expr_eq(typ, field.name, str(counter)))
                counter += 1

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
        return (u'{} {} = {};'.format(typ, name, value))
    def _expr_st(self, typ, name):
        return (u'{} {};'.format(typ, name))
=======
=======
            print(data)
>>>>>>> Added nesting
            if isinstance(data, Struct):
                self.emit(self._obj_start("message " + data.name))
                self._generate_message_cont(data)
                self.emit(self._obj_end())
                self.emit()


    def _generate_message_cont(self, msg):
        counter = 0
        with self.indent():
            for field in msg.fields:
                typ = map_stone_type_to_proto(field.data_type) if is_primitive_data(field.data_type) else field.data_type.name
                self.emit(self._expr_eq(typ, field.name, str(counter)))
                counter += 1

<<<<<<< HEAD
    def _generate_message_end(self):
        self.emit(u'}')
<<<<<<< HEAD
>>>>>>> Mapping for basic data types
=======
>>>>>>> Basic Message expression
=======
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
        return (u'{} {} = {};'.format(typ, name, value))
    def _expr_st(self, typ, name):
        return (u'{} {};'.format(typ, name))
>>>>>>> Added nesting
