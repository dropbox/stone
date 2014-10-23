from babelapi.data_type import (
    Binary,
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
from babelapi.generator.generator import CodeGeneratorMonolingual
from babelapi.lang.python import PythonTargetLanguage

base = """\
import copy
import types

from .dropbox import assert_only_one, Dropbox, Namespace

"""

class ASPGenerator(CodeGeneratorMonolingual):
    """A generator for arg_struct_parser definitions."""

    lang = PythonTargetLanguage()

    def generate(self):
        """Generates a module for each namespace."""
        for namespace in self.api.namespaces.values():
            with self.output_to_relative_path('base_{}.py'.format(namespace.name)):
                self._generate_base_namespace_module(namespace)

    def _generate_base_namespace_module(self, namespace):
        """Creates a module for the namespace. All data types are represented
        as classes. The operations are added to a class that takes the name of
        the namespace."""
        self.emit(base)
        for data_type in namespace.linearize_data_types():
            if isinstance(data_type, Struct):
                self._generate_struct_class(data_type)
            elif isinstance(data_type, Union):
                self._generate_union_class(data_type)
            else:
                raise TypeError('Cannot handle type %r' % type(data_type))

        self.emit_line('class {}(Namespace):'.format(self.lang.format_class(namespace.name)))
        with self.indent():
            for operation in namespace.operations:
                self._generate_operation(namespace, operation)

    def _class_name_for_data_type(self, data_type):
        return self.lang.format_class(data_type.name)

    def _class_declaration_for_data_type(self, data_type):
        if data_type.super_type:
            extends = self._class_name_for_data_type(data_type.super_type)
        else:
            extends = 'object'
        return 'class {}({}):'.format(self._class_name_for_data_type(data_type), extends)

    def _is_instance_type(self, data_type):
        if isinstance(data_type, (UInt32, UInt64, Int32, Int64)):
            return '(int, long)'
        elif isinstance(data_type, String):
            return 'types.StringTypes'
        else:
            return self.lang.format_type(data_type)

    def _is_instance_full_type(self, data_type):
        if isinstance(data_type, (UInt32, UInt64, Int32, Int64)):
            return '(int, long)'
        elif isinstance(data_type, String):
            return 'types.StringTypes'
        elif isinstance(data_type, CompositeType):
            return 'dropbox.data_types.{}'.format(self.lang.format_type(data_type))
        else:
            return self.lang.format_type(data_type)

    def _field_with_doc_exists(self, fields):
        """Whether at least one field in the list of fields has documentation."""
        for field in fields:
            if field.doc:
                return True
        else:
            return False

    def _data_type_has_doc(self, data_type):
        """Use this to determine whether it makes sense to create a stub for
        documentation. For example, in Python, you only want to create a triple
        quote doc section if the data_type has a doc, or one of its fields does.
        Otherwise, you'll make an empty doc string."""
        return bool(data_type.doc) or self._field_with_doc_exists(data_type.fields)

    def _generate_struct_class(self, data_type):
        self.emit_line(self._class_declaration_for_data_type(data_type))
        with self.indent():
            if data_type.doc:
                self.emit_line('"""')
                self.emit_wrapped_lines(data_type.doc)
                self.emit_line('"""')
            self.emit_empty_line()

            self.emit_line('def __init__', trailing_newline=False)
            args = ['self']
            for field in data_type.all_fields:
                if field.optional:
                    args.append('{}=None'.format(field.name))
                else:
                    args.append(field.name)
            args.append('**kwargs')
            self._generate_func_arg_list(args, compact=True)
            self.emit(':')
            self.emit_empty_line()

            with self.indent():
                # Write docs for all fields
                if data_type.all_fields:
                    self.emit_line('"""')
                    self.emit_line('Args:')
                    with self.indent():
                        for field in data_type.fields:
                            if field.doc:
                                field_doc = '{} ({}): {}'.format(
                                    field.name,
                                    self.lang.format_type(field.data_type),
                                    field.doc,
                                )
                                self.emit_wrapped_lines(field_doc,
                                                        prefix='    ',
                                                        first_line_prefix=False)
                    self.emit_line('"""')

                # Call the parent constructor if a super type exists
                if data_type.super_type:
                    self.emit_indent()
                    class_name = self._class_name_for_data_type(data_type)
                    self.emit('super({}, self).__init__('.format(class_name))
                    if data_type.super_type.all_fields:
                        self.emit_empty_line()
                        with self.indent(4):
                            for field in data_type.super_type.all_fields:
                                self.emit_line('{},'.format(field.name))
                        self.emit_line(')')
                        self.emit_empty_line()
                    else:
                        self.emit_(')')
                        self.emit_empty_line()

                # Assign each field
                if data_type.fields:
                    for field in data_type.fields:
                        # FIXME: Replace True with check of whether union has unique value types
                        if isinstance(field.data_type, Union) and True:
                            for variant in field.data_type.fields:
                                if isinstance(variant, SymbolField):
                                    self.emit_line('if {0} == {1}.{2}:'.format(
                                        field.name,
                                        self._class_name_for_data_type(field.data_type),
                                        self.lang.format_class(variant.name),
                                    ))
                                    with self.indent():
                                        self.emit_line('self.{0} = {1}({2}=True)'.format(
                                            field.name,
                                            self._class_name_for_data_type(field.data_type),
                                            self.lang.format_variable(variant.name),
                                        ))
                                else:
                                    self.emit_line('if isinstance({0}, {1}.{2}):'.format(
                                        field.name,
                                        self._class_name_for_data_type(field.data_type),
                                        self.lang.format_class(variant.name),
                                    ))
                                    with self.indent():
                                        self.emit_line('self.{0} = {1}({2}={0})'.format(
                                            field.name,
                                            self._class_name_for_data_type(field.data_type),
                                            self.lang.format_variable(variant.name),
                                        ))
                        else:
                            assert_type = "assert isinstance({0}, {1}), '{0} must be of type {2}'".format(
                                field.name,
                                self._is_instance_type(field.data_type),
                                self._is_instance_full_type(field.data_type),
                            )
                            if field.nullable or field.optional:
                                # We conflate nullability and optionality in Python
                                self.emit_line('if {} is not None:'.format(field.name))
                                with self.indent():
                                    self.emit_line(assert_type)
                            else:
                                self.emit_line(assert_type)
                            self.emit_line('self.{0} = {0}'.format(field.name))
                            self.emit_empty_line()
                else:
                    self.emit_line('pass')
                    self.emit_empty_line()

            # The special __repr__() function will return a string of the class
            # name, and if the class has fields, the first field as well.
            self.emit_line('def __repr__(self):')
            with self.indent():
                if data_type.fields:
                    self.emit_line("return '{}(%r)' % self.{}".format(
                        self._class_name_for_data_type(data_type),
                        data_type.fields[0].name,
                    ))
                else:
                    self.emit_line("return '{}()'".format(self._class_name_for_data_type(data_type)))
            self.emit_empty_line()

            # The from_json() function will convert a Python dictionary object
            # that presumably was constructed from JSON into a Python object
            # of the correct type.
            self.emit_line('@classmethod')
            self.emit_line('def from_json(cls, obj):')
            with self.indent():
                if data_type.all_fields:
                    self.emit_line('obj = copy.copy(obj)')
                for field in data_type.all_fields:
                    if isinstance(field.data_type, CompositeType):
                        composite_assignment = "obj['{0}'] = {1}.from_json(obj['{0}'])".format(
                            field.name,
                            self._class_name_for_data_type(field.data_type),
                        )
                        self.emit_line(composite_assignment)
                self.emit_line('return {}(**obj)'.format(self._class_name_for_data_type(data_type)))
                self.emit_empty_line()

            # The to_json() function will convert a Python object into a
            # dictionary that can be serialized into JSON.
            self.emit_line('def to_json(self):')
            with self.indent():
                self.emit_line('d = dict', trailing_newline=False)
                args = []
                for field in data_type.all_required_fields:
                    if isinstance(field.data_type, CompositeType):
                        args.append('{0}=self.{0}.to_json()'.format(field.name))
                    else:
                        # TODO: Need to handle other types like datetime,
                        # and options like nullable
                        args.append('{0}=self.{0}'.format(field.name))
                self._generate_func_arg_list(args, compact=True)
                self.emit_empty_line()
                for field in data_type.all_optional_fields:
                    self.emit_line('if self.{}:'.format(field.name))
                    with self.indent():
                        self.emit_line("d['{0}'] = self.{0}".format(field.name))
                self.emit_line('return d')

            self.emit_empty_line()

    def _generate_union_class(self, data_type):
        self.emit_line(self._class_declaration_for_data_type(data_type))
        with self.indent():
            if data_type.doc:
                self.emit_line('"""')
                self.emit_wrapped_lines(data_type.doc)
                self.emit_line('"""')
            self.emit_empty_line()

            for field in data_type.fields:
                if isinstance(field, SymbolField):
                    self.emit_line('{} = object()'.format(self.lang.format_class(field.name)))
                elif isinstance(field.data_type, CompositeType):
                    self.emit_line('{0} = {1}'.format(self.lang.format_class(field.name),
                                                      self._class_name_for_data_type(field.data_type)))
                else:
                    raise ValueError('Only symbols and composite types for union fields.')
            self.emit_empty_line()

            self.emit_line('def __init__', trailing_newline=False)
            args = ['self']
            for field in data_type.fields:
                args.append('{}=None'.format(field.name))
            args.append('**kwargs')
            self._generate_func_arg_list(args, compact=True)
            self.emit(':')
            self.emit_empty_line()

            with self.indent():
                if data_type.fields:
                    if self._data_type_has_doc(data_type):
                        self.emit_line('"""')
                        if data_type.doc:
                            self.emit_wrapped_lines(data_type.doc)
                            self.emit_empty_line()
                        self.emit_wrapped_lines('Only one argument may be specified.')
                        self.emit_empty_line()
                        if self._field_with_doc_exists(data_type.fields):
                            self.emit_line('Args:')
                            with self.indent():
                                for field in data_type.fields:
                                    if field.doc:
                                        self.emit_wrapped_lines(field.name + ': ' + field.doc,
                                                                prefix='    ',
                                                                first_line_prefix=False)
                        self.emit_line('"""')

                    self.emit_line('assert_only_one', trailing_newline=False)
                    args = []
                    for field in data_type.fields:
                        args.append('{0}={0}'.format(field.name))
                    args.append('**kwargs')
                    self._generate_func_arg_list(args)
                    self.emit_empty_line()

                    for field in data_type.fields:
                        self.emit_line('self.{} = None'.format(self.lang.format_variable(field.name)))
                    self.emit_empty_line()

                    for field in data_type.fields:
                        if not isinstance(field, SymbolField):
                            assert_type = "assert isinstance({0}, {1}), '{0} must be of type {2}'".format(
                                field.name,
                                self._is_instance_type(field.data_type),
                                self._is_instance_full_type(field.data_type),
                            )
                        else:
                            assert_type = "assert isinstance({0}, {1}), '{0} must be of type {2}'".format(
                                field.name,
                                'bool',
                                'bool',
                            )
                        self.emit_line('if {} is not None:'.format(field.name))
                        with self.indent():
                            self.emit_line(assert_type)
                            self.emit_line('self.{0} = {0}'.format(field.name))
                            self.emit_line("self._tag = '{}'".format(field.name))
                        self.emit_empty_line()
                else:
                    self.emit_line('pass')
                    self.emit_empty_line()

            # The from_json() function will convert a Python dictionary object
            # that presumably was constructed from JSON into a Python object
            # of the correct type.
            self.emit_line('@classmethod')
            self.emit_line('def from_json(self, obj):')
            with self.indent():
                if data_type.all_fields:
                    self.emit_line('obj = copy.copy(obj)')
                self.emit_line("assert len(obj) == 1, 'One key must be set, not %d' % len(obj)")
                first = True
                for field in data_type.all_fields:
                    if isinstance(field, SymbolField):
                        self.emit_line("if obj == '{}':".format(field.name))
                        with self.indent():
                            self.emit_line('return obj')
                    elif isinstance(field.data_type, CompositeType):
                        self.emit_line("if '{}' in obj:".format(field.name))
                        with self.indent():
                            composite_assignment = "obj['{0}'] = {1}.from_json(obj['{0}'])".format(
                                field.name,
                                self._class_name_for_data_type(field.data_type),
                            )
                            self.emit_line(composite_assignment)
                    else:
                        # FIXME: Blah exception
                        raise Exception('Unrecognized')
                self.emit_line('return {}(**obj)'.format(self._class_name_for_data_type(data_type)))
                self.emit_empty_line()

            # The to_json() function will convert a Python object into a
            # dictionary that can be serialized into JSON.
            self.emit_line('def to_json(self):')
            with self.indent():
                for field in data_type.all_fields:
                    self.emit_line("if self._tag == '{}':".format(field.name))
                    with self.indent():
                        if isinstance(field, SymbolField):
                            self.emit_line('return self._tag')
                        else:
                            self.emit_line('return dict({0}=self.{0}.to_json())'.format(field.name))
            self.emit_empty_line()

            # The special __repr__() function will return a string of the class
            # name, and the selected tag
            self.emit_line('def __repr__(self):')
            with self.indent():
                if data_type.fields:
                    self.emit_line("return '{}(%r)' % self._tag".format(
                        self._class_name_for_data_type(data_type),
                    ))
                else:
                    self.emit_line("return '{}()'".format(self._class_name_for_data_type(data_type)))
            self.emit_empty_line()

    def _has_binary_segment(self, segmentation):
        """If an operation has Binary specified as the second segment of a request or response,
        the payload will be in the HTTP body. Binary should never appear anywhere else in a
        segmentation."""
        return (len(segmentation.segments) == 2
                and isinstance(segmentation.segments[1].data_type, Binary))

    def _generate_operation(self, namespace, operation):
        """Generate a Python method that corresponds to an operation."""
        request_data_type = operation.request_segmentation.segments[0].data_type
        response_data_type = operation.response_segmentation.segments[0].data_type

        request_binary_body = self._has_binary_segment(operation.request_segmentation)
        response_binary_body = self._has_binary_segment(operation.response_segmentation)
        host = self._generate_op_host(operation.extras.get('host', 'api'))
        style = self._generate_op_style(operation.extras.get('style', 'rpc'))

        self._generate_operation_method_decl(operation, request_data_type, request_binary_body)

        with self.indent():
            self._generate_operation_method_docstring(operation, request_data_type, request_binary_body)

            # Code to instantiate a class for the request data type
            self.emit_line('o = {}'.format(
                self._class_name_for_data_type(request_data_type)
            ), trailing_newline=False)
            self._generate_func_arg_list([f.name for f in request_data_type.all_fields])
            self.emit_empty_line()

            # Code to make the request
            self.emit_line('r = self._dropbox.request', trailing_newline=False)
            args = [host,
                    "'{}/{}'".format(namespace.name, operation.path),
                    style,
                    'o.to_json()']
            if request_binary_body:
                args.append('f')
            else:
                args.append('None')
            self._generate_func_arg_list(args, compact=True)
            self.emit_empty_line()

            if response_binary_body:
                self.emit_line('return {}.from_json(r.obj_segment), r.binary_segment'.format(
                    self._class_name_for_data_type(response_data_type)
                ))
            else:
                self.emit_line('return {}.from_json(r.obj_segment)'.format(
                    self._class_name_for_data_type(response_data_type)
                ))
        self.emit_empty_line()

    def _generate_op_host(self, host):
        """"Convert the host specified in the spec to the appropriate Python object."""
        if host == 'content':
            return 'Dropbox.Host.API_CONTENT'
        elif host == 'notify':
            return 'Dropbox.Host.API_NOTIFY'
        elif host == 'api':
            return 'Dropbox.Host.API'
        else:
            raise ValueError('Unknown host')

    def _generate_op_style(self, style):
        """"Convert the style specified in the spec to the appropriate Python object."""
        if style == 'rpc':
            return 'Dropbox.OpStyle.RPC'
        elif style == 'download':
            return 'Dropbox.OpStyle.DOWNLOAD'
        elif style == 'upload':
            return 'Dropbox.OpStyle.UPLOAD'
        else:
            raise ValueError('Unknown operation style')

    def _generate_operation_method_decl(self, operation, request_data_type, request_binary_body):
        self.emit_line('def {}'.format(self.lang.format_method(operation.name)),
                       trailing_newline=False)
        args = ['self']
        if request_binary_body:
            args.append('f')
        for field in request_data_type.all_fields:
            if field.optional or field.nullable:
                if field.has_default:
                    args.append('{}={}'.format(field.name, self.lang.format_obj(field.default)))
                else:
                    args.append('{}=None'.format(field.name))
            else:
                args.append(field.name)
        self._generate_func_arg_list(args)
        self.emit(':')
        self.emit_empty_line()

    def _generate_operation_method_docstring(self, operation, request_data_type,
                                             request_binary_body):
        self.emit_line('"""')
        self.emit_wrapped_lines(operation.doc)
        if self._field_with_doc_exists(request_data_type.fields) or request_binary_body:
            self.emit_empty_line()
            self.emit_line('Args:')
            with self.indent():
                if request_binary_body:
                    self.emit_wrapped_lines('f: A string or file-like obj of data.')
                for field in request_data_type.fields:
                    if field.doc:
                        self.emit_wrapped_lines(field.name + ': ' + field.doc,
                                                prefix='    ',
                                                first_line_prefix=False)
        error_data_type = operation.error_data_type
        if error_data_type and error_data_type.fields:
            self.emit_empty_line()
            self.emit_line('Raises:')
            with self.indent():
                self.emit_line('ApiError with the following codes:')
                with self.indent():
                    for field in error_data_type.fields:
                        if field.doc:
                            self.emit_wrapped_lines('{}: {}'.format(field.name, field.doc),
                                                    prefix='    ', first_line_prefix=False)
                        else:
                            self.emit_line(field.name)
        self.emit_line('"""')

    def _generate_func_arg_list(self, args, compact=True):
        self.emit('(')
        if len(args) == 0:
            self.emit(')')
            return
        elif len(args) == 1:
            self.emit(args[0])
            self.emit(')')
        else:
            if compact:
                with self.indent_to_cur_col():
                    args = args[:]
                    self.emit(args.pop(0))
                    self.emit(',')
                    self.emit_empty_line()
                    for (i, arg) in enumerate(args):
                        if i == len(args) - 1:
                            self.emit_line(arg, trailing_newline=False)
                        else:
                            self.emit_line(arg + ',')
                    self.emit(')')
            else:
                self.emit_empty_line()
                with self.indent():
                    for arg in args:
                        self.emit_line(arg + ',')
                self.emit_indent()
                self.emit(')')
