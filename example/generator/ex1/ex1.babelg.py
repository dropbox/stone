from babelapi.generator import CodeGenerator

class ExampleGenerator(CodeGenerator):
    def generate(self):
        """Generates a file that lists each namespace."""
        with self.output_to_relative_path('ex1.out'):
            for namespace in self.api.namespaces.values():
                self.emit(namespace.name)
