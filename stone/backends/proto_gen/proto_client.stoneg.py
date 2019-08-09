from stone.backend import CodeBackend
from stone.ir import(
    Struct,
    StructField,
)
from proto_type_mapping import map_stone_type_to_proto

class ProtoBackend(CodeBackend):
    def generate(self, api):
        with self.output_to_relative_path('test.proto'):
            for namespace in api.namespaces.values():
                self._create_package(namespace.name)
                self._generate_messages(namespace)

    def _create_package(self, val):
        self.emit("package " + val + ";")
        self.emit()

    def _generate_messages(self, namespace):
        for data in namespace.data_types:
            if isinstance(data, Struct):
                self._generate_message_decl(data)
                self._generate_message_cont(data)
                self._generate_message_end()
        print(namespace.data_types)

    def _generate_message_decl(self, msg):
        print(msg.name)
        self.emit("message " + msg.name + " " +u'{')

    def _generate_message_cont(self, msg):
        int counter = 0
        with self.indent():
            for field in msg.fields:
                print(map_stone_type_to_proto(field.data_type))
                self.emit(map_stone_type_to_proto(field.data_type) + " " + field.name + "=" + counter)
                counter += 1

    def _generate_message_end(self):
        self.emit(u'}')
