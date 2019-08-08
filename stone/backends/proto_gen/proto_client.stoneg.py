from stone.backend import CodeBackend
from stone.ir import(
    Struct,
    StructField,
)

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
        with self.indent():
            for field in msg.fields:
                self.emit(field.data_type.name + "\t" + field.name)

    def _generate_message_end(self):
        self.emit(u'}')