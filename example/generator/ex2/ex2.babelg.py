from babelapi.generator import CodeGenerator

class ExamplePythonGenerator(CodeGenerator):
    def generate(self):
        """Generates a module for each namespace."""
        for namespace in self.api.namespaces.values():
            # One module per namespace is created. The module takes the name
            # of the namespace.
            with self.output_to_relative_path('{}.py'.format(namespace.name)):
                self._generate_namespace_module(namespace)

    def _generate_namespace_module(self, namespace):
        self.emit('def noop():')
        with self.indent():
            self.emit('pass')
