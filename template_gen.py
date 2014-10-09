from contextlib import contextmanager
import re

from babelsdk.data_type import (
    Boolean,
    CompositeType,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    String,
    Struct,
    SymbolField,
    Timestamp,
    UInt32,
    UInt64,
    Union,
)
from babelsdk.lang.python import PythonTargetLanguage

base = """
from dropbox import arg_struct_parser as asp

# We use an identity function because we don't need to mutate the return value
# of the parser in any way.
def identity(x):
    return x

"""

_split_words_capitalization_re = re.compile(
    '^[a-z0-9]+|[A-Z][a-z0-9]+|[A-Z]+(?=[A-Z][a-z0-9])|[A-Z]+$'
)

_split_words_dashes_re = re.compile('[-_]+')

def split_words(words):
    """
    Splits a word based on capitalization, dashes, or underscores.
        Example: 'GetFile' -> ['Get', 'File']
    """
    all_words = []
    for word in re.split(_split_words_dashes_re, words):
        vals = _split_words_capitalization_re.findall(word)
        if vals:
            all_words.extend(vals)
        else:
            all_words.append(word)
    return all_words

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

    def emit_empty_line(self):
        self.emit('\n')

    def _validator_name(self, namespace, data_type):
        return '{}_{}_validator'.format(
            namespace.name,
            self.python.format_variable(split_words(data_type.name)),
        )

    def _struct_validator_declaration(self, namespace, data_type):
        return '{} = asp.Record('.format(self._validator_name(namespace, data_type))

    def _union_validator_declaration(self, namespace, data_type):
        return '{} = asp.Variant('.format(self._validator_name(namespace, data_type))

    def _create_function_args(self, *args, **kwargs):
        func_args = [self.python.format_obj(arg) for arg in args]
        func_args.extend(['{}={}'.format(k, self.python.format_obj(v))
                          for k, v in kwargs.items()])
        return ', '.join(func_args)

    def _resolve_asp_type(self, namespace, field):
        if isinstance(field, SymbolField):
            return 'object()'
        else:
            is_list = isinstance(field.data_type, List)
            if is_list:
                data_type = field.data_type.data_type
            else:
                data_type = field.data_type
            if isinstance(data_type, CompositeType):
                return self._validator_name(namespace, data_type)
            elif isinstance(data_type, String):
                s = 'asp.StringB({})'.format(
                    self._create_function_args(
                        min_length=data_type.min_length,
                        max_length=data_type.max_length,
                        regex=data_type.pattern,
                    )
                )
            elif isinstance(data_type, (Int32, Int64)):
                s = 'asp.Int()'
            elif isinstance(data_type, (UInt32, UInt64)):
                s = 'asp.Nat()'
            elif isinstance(data_type, (Float32, Float64)):
                s = 'asp.Float()'
            elif isinstance(data_type, Boolean):
                s = 'asp.Boolean()'
            elif isinstance(data_type, Timestamp):
                s = 'asp.Timestamp()'
            else:
                #return None
                print is_list, isinstance(data_type, (Float32, Float64))
                raise Exception(data_type)
            if is_list:
                s = 'asp.List({})'.format(s)
            if field.nullable:
                return 'Nullable({})'.format(s)
            else:
                return s

    def generate(self):
        self.output = []
        for namespace in self.api.namespaces.values():
            for data_type in namespace.linearize_data_types():
                if isinstance(data_type, Struct):
                    self.emit_line(self._struct_validator_declaration(namespace, data_type))
                    with self.indent():
                        for field in data_type.fields:
                            if field.has_default:
                                self.emit_line("('{}', {}, {}),".format(
                                    field.name,
                                    self._resolve_asp_type(namespace, field),
                                    self.python.format_obj(field.default))
                                )
                            else:
                                self.emit_line("('{}', {}),".format(
                                    field.name,
                                    self._resolve_asp_type(namespace, field))
                                )
                    self.emit_line(')')
                    self.emit_empty_line()
                elif isinstance(data_type, Union):
                    self.emit_line(self._union_validator_declaration(namespace, data_type))
                    with self.indent():
                        for field in data_type.fields:
                            self.emit_line("('{}', identity, {}),".format(
                                field.name,
                                self._resolve_asp_type(namespace, field)),
                            )
                    self.emit_line(')')
                    self.emit_empty_line()
                else:
                    raise ValueError()

        return base + ''.join(self.output)
