from babelsdk.lang.python import PythonTargetLanguage

from contextlib import contextmanager

base = """
from dropbox import arg_struct_parser as asp

# We use an identity function because we don't need to mutate the return value
# of the parser in any way.
def identity(x):
    return x

"""

class Indenter(object):
    def __init__(self, gen, dent):
        print 'created indenter'
        self.gen = gen
        self.dent = dent

    def __enter__(self):
        self.gen.cur_indent += self.dent

    def __exit__(self):
        self.gen.cur_indent -= self.dent

class TemplateGenerator(object):
    def __init__(self, api):
        self.api = api
        self.output = []
        self.python = PythonTargetLanguage()

        self.indent_stack = []
        self.cur_indent = 0
        self.tabs_for_indents = False

    #def indent(self, dent):
    #    return Indenter(self, dent)

    @contextmanager
    def indent(self, dent=None):
        assert dent != 0, 'Cannot specify relative indent of 0'
        if dent is None:
            if self.tabs_for_indents:
                dent = 1
            else:
                dent = 4
        self.indent_stack.append(dent)
        self.cur_indent += dent
        yield
        self.indent_stack.pop()
        self.cur_indent -= dent

    def make_indent(self):
        if self.tabs_for_indents:
            return '\t' * self.cur_indent
        else:
            return ' ' * self.cur_indent

    def emit_indent(self):
        self.emit(self.make_indent())

    def emit(self, blob):
        #self.output.append(self.make_indent())
        self.output.append(blob)

    def emit_line(self, blob):
        self.emit_indent()
        self.emit(blob)
        self.emit('\n')

    def generate(self):
        self.output = []
        for namespace in self.api.namespaces.values():
            for data_type in namespace.linearize_data_types():
                self.emit_line('{}_{}_validator = asp.Record('.format(namespace.name, data_type.name))
                with self.indent():
                    for field in data_type.fields:
                        self.emit_line("('{}', asp.{}),".format(field.name, field.data_type.name))
                self.emit_line(')')

        return base + ''.join(self.output)
