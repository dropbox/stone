from stone.backend import CodeBackend


class ProtoBackend(CodeBackend):
    def generate(self, api):
        with self.output_to_relative_path('test.proto'):
            for namespace in api.namespaces.values():
                self._create_package(namespace.name)
                #self._generate_messages(namespace)

    def _create_package(self, val):
        self.emit("package " + val + ";")
