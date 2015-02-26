from babelapi.data_type import Struct
from babelapi.generator import CodeGeneratorMonolingual
from babelapi.lang.python import PythonTargetLanguage

class ExamplePythonGenerator(CodeGeneratorMonolingual):

    # PythonTargetLanguage has helper methods for formatting class, obj
    # and variable names (some languages use underscores to separate words,
    # others use camelcase).
    lang = PythonTargetLanguage()

    def generate(self):
        """Generates a module for each namespace."""
        for namespace in self.api.namespaces.values():
            # One module per namespace is created. The module takes the name
            # of the namespace.
            with self.output_to_relative_path('{}.py'.format(namespace.name)):
                self._generate_namespace_module(namespace)

    def _generate_namespace_module(self, namespace):
        for data_type in namespace.linearize_data_types():
            if not isinstance(data_type, Struct):
                # Do not handle Union types
                continue

            # Define a class for each struct
            class_def = 'class {}(object):'.format(self.lang.format_class(data_type.name))
            self.emit_line(class_def)

            with self.indent():
                if data_type.doc:
                    self.emit_line('"""')
                    self.emit_wrapped_lines(data_type.doc)
                    self.emit_line('"""')

                self.emit_empty_line()

                # Define constructor to take each field
                self.emit_line('def __init__', trailing_newline=False)
                args = ['self']
                for field in data_type.fields:
                    args.append(self.lang.format_variable(field.name))
                self._generate_func_arg_list(args)
                self.emit(':')
                self.emit_empty_line()

                with self.indent():
                    if data_type.fields:
                        # Body of init should assign all init vars
                        for field in data_type.fields:
                            if field.doc:
                                self.emit_wrapped_lines(field.doc, prefix='# ')
                            member_name = self.lang.format_variable(field.name)
                            self.emit_line('self.{0} = {0}'.format(member_name))
                    else:
                        self.emit_line('pass')
            self.emit_empty_line()
