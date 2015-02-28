"""
BabelAPI Code Generator for the Dropbox Python v2 SDK.

TODO: With a little bit more abstraction and better modularity, this could
become the general "Babel-Python" generator, and wouldn't have to be Dropbox-
specific at all.
"""

import re
from babelapi.data_type import (
    CompositeType,
    Int32,
    Int64,
    String,
    SymbolField,
    UInt32,
    UInt64,
)
from babelapi.data_type import (
    is_composite_type,
    is_null_type,
    is_struct_type,
    is_union_type,
)
from babelapi.generator import CodeGeneratorMonolingual
from babelapi.lang.python import PythonTargetLanguage

base = """\
import copy
import numbers
import six

from .dropbox import Dropbox, Namespace
from .util import assert_only_one

"""

# Matches format of Babel doc tags
doc_sub_tag_re = re.compile(':(?P<tag>[A-z]*):`(?P<val>.*?)`')

class DbxPythonSDKGenerator(CodeGeneratorMonolingual):
    """Generates Python modules for the Dropbox Python v2 SDK that implement
    the data types and routes defined in the spec."""

    lang = PythonTargetLanguage()

    def generate(self):
        """
        Generates a module for each namespace.

        Each namespace will have Python classes to represent structs and unions
        in the Babel spec. The namespace will also have a class of the same
        name but prefixed with "Base" that will have methods that represent
        the routes specified in the Babel spec.
        """
        for namespace in self.api.namespaces.values():
            with self.output_to_relative_path('base_{}.py'.format(namespace.name)):
                self._generate_base_namespace_module(namespace)

    def _generate_base_namespace_module(self, namespace):
        """Creates a module for the namespace. All data types are represented
        as classes. The routes are added to a class that takes the name of the
        namespace."""
        self.emit(base)
        for data_type in namespace.linearize_data_types():
            if is_struct_type(data_type):
                self._generate_struct_class(data_type)
            elif is_union_type(data_type):
                self._generate_union_class(data_type)
            else:
                raise TypeError('Cannot handle type %r' % type(data_type))

        self.emit_line('class Base{}(Namespace):'.format(self.lang.format_class(namespace.name)))
        with self.indent():
            self.emit_line('"""Methods for routes in the {} namespace"""'.format(namespace.name))
            self.emit_empty_line()
            for route in namespace.routes:
                self._generate_route(namespace, route)

    def emit_wrapped_indented_lines(self, s):
        """Emits wrapped lines. All lines are the first are indented."""
        self.emit_wrapped_lines(s,
                                prefix='    ',
                                first_line_prefix=False)

    def docf(self, doc):
        """
        Substitutes tags in Babel docs with their Python-doc-friendly
        counterparts. A tag has the following format:

        :<tag>:`<value>`

        Example tags are 'route' and 'struct'.
        """
        if not doc:
            return
        for match in doc_sub_tag_re.finditer(doc):
            matched_text = match.group(0)
            tag = match.group('tag')
            val = match.group('val')
            if tag == 'struct':
                doc = doc.replace(matched_text, ':class:`{}`'.format(val))
            elif tag == 'route':
                doc = doc.replace(matched_text, ':meth:`{}`'.format(self.lang.format_method(val)))
            elif tag == 'link':
                anchor, link = val.rsplit(' ', 1)
                doc = doc.replace(matched_text, '`{} <{}>`_'.format(anchor, link))
            elif tag == 'val':
                doc = doc.replace(matched_text, '{}'.format(self.lang.format_obj(val)))
            else:
                doc = doc.replace(matched_text, '``{}``'.format(val))
        return doc

    #
    # Struct Types
    #

    def _generate_struct_class(self, data_type):
        """Defines a Python class that represents a struct in Babel."""
        self.emit_line(self._class_declaration_for_data_type(data_type))
        with self.indent():
            if data_type.doc:
                self.emit_line('"""')
                self.emit_wrapped_lines(self.docf(data_type.doc))
                self.emit_line('"""')
            self.emit_empty_line()

            self._generate_struct_class_init(data_type)
            self._generate_struct_class_from_json(data_type)
            self._generate_struct_class_to_json(data_type)
            self._generate_struct_class_repr(data_type)

    def _format_type_in_doc(self, data_type):
        if is_null_type(data_type):
            return 'None'
        elif is_composite_type(data_type):
            return ':class:`{}`'.format(self.lang.format_type(data_type))
        else:
            return self.lang.format_type(data_type)

    def _generate_docstring_for_func(self, input_data_type, return_data_type=None,
                                     error_data_type=None, overview=None,
                                     extra_request_args=None, extra_return_arg=None):
        """
        Generates a docstring for a function or method.

        This function is versatile. It will create a docstring using all the
        data that is provided.

        :param input_data_type: The data type describing the inputs to the
            function. Each field of the data type will be described as an input
            parameter of the function.
        :param return_data_type: The data type describing the output.
        :param error_data_type: A data type describing the response in the case
            of an error.
        :param str overview: A description of the function that will be placed
            at the top of the docstring.
        :param extra_request_args: List of tuples [(field name, field type, field doc), ...]
            that describes any additional arguments that aren't specified in the
            input_data_type.
        :param str extra_return_arg: Name of an additional return type that. If
            this is specified, it is assumed that the return of the function
            will be a tuple of return_data_type and extra_return-arg.
        """
        fields = input_data_type.fields
        if not fields and not overview:
            # If we don't have an overview or fields, we skip because the
            # documentation is considered too incomplete.
            return

        self.emit_line('"""')
        if overview:
            self.emit_wrapped_lines(overview)

        if extra_request_args or fields:
            if overview:
                # Add a blank line if we had an overview
                self.emit_empty_line()
            if extra_request_args:
                for name, data_type_name, doc in extra_request_args:
                    if data_type_name:
                        field_doc = ':param {} {}: {}'.format(data_type_name, name, doc)
                        self.emit_wrapped_lines(field_doc)
                    else:
                        self.emit_wrapped_indented_lines(':param {}: {}'.format(name, doc))
            for field in fields:
                if field.doc:
                    if isinstance(field, SymbolField):
                        field_doc = ':param bool {}: {}'.format(field.name, self.docf(field.doc))
                    elif isinstance(field.data_type, CompositeType):
                        field_doc = ':param {}: {}'.format(field.name, self.docf(field.doc))
                    else:
                        field_doc = ':param {} {}: {}'.format(
                            self._format_type_in_doc(field.data_type),
                            field.name,
                            self.docf(field.doc),
                        )
                    self.emit_wrapped_indented_lines(field_doc)
                    if is_composite_type(field.data_type):
                        self.emit_line(':type {}: {}'.format(
                            field.name,
                            self._format_type_in_doc(field.data_type),
                        ))
                else:
                    if isinstance(field, SymbolField):
                        field_doc = ':type {}: bool'.format(
                            field.name,
                            self._format_type_in_doc(field.data_type)
                        )
                        self.emit_wrapped_indented_lines(field_doc)
                    else:
                        field_doc = ':type {}: {}'.format(
                            field.name,
                            self._format_type_in_doc(field.data_type)
                        )
                        self.emit_wrapped_lines(field_doc)

        if return_data_type:
            if overview and not (extra_request_args or fields):
                self.emit_empty_line()

            if is_null_type(return_data_type):
                self.emit_line(':rtype: None', trailing_newline=False)
            else:
                self.emit_line(':rtype: {}'.format(self._format_type_in_doc(return_data_type)),
                               trailing_newline=False)
            if extra_return_arg:
                # Any extra return arg is specified as the second element of a tuple.
                self.emit(', {}'.format(extra_return_arg))
            self.emit_empty_line()

        if error_data_type and not is_null_type(error_data_type) and error_data_type.fields:
            self.emit_line(':raises: :class:`dropbox.exceptions.ApiError`')
            self.emit_empty_line()
            self.emit_line('Error codes:')
            with self.indent():
                for field in error_data_type.fields:
                    if field.doc:
                        self.emit_wrapped_indented_lines('{}: {}'.format(
                            field.name,
                            self.docf(field.doc)
                        ))
                    else:
                        self.emit_line(field.name)
        self.emit_line('"""')

    def _generate_struct_class_init(self, data_type):
        """Generates constructor for struct."""
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
            self._generate_docstring_for_func(data_type)

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
                    if (is_union_type(field.data_type)
                            and field.data_type.unique_field_data_types()):

                        # This is an optimization for the developer experience.
                        # Without optimzation, the developer needs to instantiate a
                        # class representing the tagged union, and pass in an
                        # instantiated object for the tag as a kwarg. With this,
                        # just the instantiated object needs to be passed in
                        # because the tag can be determined from the type.
                        #
                        # Difference between:
                        # dbx.files.upload(mode=UploadMode(overwrite=UploadMode.Overwrite))
                        # and
                        # dbx.files.upload(mode=UploadMode.Overwrite)
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
                        self.emit_empty_line()
                    else:
                        assert_type = ("assert isinstance({0}, {1}), '{0} must be of type {1}'"
                            .format(
                                field.name,
                                self._is_instance_type(field.data_type)))
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

    def _generate_struct_class_repr(self, data_type):
        """The special __repr__() function will return a string of the class
        name, and if the class has fields, the first field as well."""
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

    def _generate_struct_class_from_json(self, data_type):
        """The from_json() function will convert a Python dictionary object
        that presumably was constructed from JSON into a Python object
        of the correct type."""
        self.emit_line('@classmethod')
        self.emit_line('def from_json(cls, obj):')
        with self.indent():
            if data_type.all_fields:
                self.emit_line('obj = copy.copy(obj)')
            for field in data_type.all_fields:
                if is_composite_type(field.data_type):
                    composite_assignment = "obj['{0}'] = {1}.from_json(obj['{0}'])".format(
                        field.name,
                        self._class_name_for_data_type(field.data_type),
                    )
                    self.emit_line(composite_assignment)
            self.emit_line('return {}(**obj)'.format(self._class_name_for_data_type(data_type)))
        self.emit_empty_line()

    def _generate_struct_class_to_json(self, data_type):
        """The to_json() function will convert a Python object into a
        dictionary that can be serialized into JSON."""
        self.emit_line('def to_json(self):')
        with self.indent():
            self.emit_line('d = dict', trailing_newline=False)
            args = []
            for field in data_type.all_required_fields:
                if is_composite_type(field.data_type):
                    args.append('{0}=self.{0}.to_json()'.format(field.name))
                else:
                    # TODO: Need to handle other types like datetime/timestamp
                    args.append('{0}=self.{0}'.format(field.name))
            self._generate_func_arg_list(args, compact=True)
            self.emit_empty_line()
            for field in data_type.all_optional_fields:
                self.emit_line('if self.{}:'.format(field.name))
                with self.indent():
                    if is_composite_type(field.data_type):
                        self.emit_line("d['{0}'] = self.{0}.to_json()".format(field.name))
                    else:
                        self.emit_line("d['{0}'] = self.{0}".format(field.name))
            self.emit_line('return d')
        self.emit_empty_line()

    def _class_name_for_data_type(self, data_type):
        return self.lang.format_class(data_type.name)

    def _class_declaration_for_data_type(self, data_type):
        if data_type.super_type:
            extends = self._class_name_for_data_type(data_type.super_type)
        else:
            extends = 'object'
        return 'class {}({}):'.format(self._class_name_for_data_type(data_type), extends)

    def _is_instance_type(self, data_type):
        """The Python types to use in a call to isinstance() for the specified
        Babel data_type."""
        if isinstance(data_type, (UInt32, UInt64, Int32, Int64)):
            return 'numbers.Integral'
        elif isinstance(data_type, String):
            return 'six.string_types'
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

    #
    # Tagged Union Types
    #

    def _generate_union_class(self, data_type):
        """Defines a Python class that represents a union in Babel."""
        self.emit_line(self._class_declaration_for_data_type(data_type))
        with self.indent():
            if data_type.doc:
                self.emit_line('"""')
                self.emit_wrapped_lines(self.docf(data_type.doc))
                self.emit_empty_line()
                for field in data_type.fields:
                    if isinstance(field, SymbolField):
                        ivar_doc = ':ivar {}: {}'.format(self.lang.format_class(field.name),
                                                         self.docf(field.doc))
                    elif is_composite_type(field.data_type):
                        ivar_doc = ':ivar {}: {}'.format(
                            self.lang.format_class(field.name),
                            self.docf(field.doc),
                        )
                    self.emit_wrapped_indented_lines(ivar_doc)
                self.emit_line('"""')
            self.emit_empty_line()

            for field in data_type.fields:
                if isinstance(field, SymbolField):
                    self.emit_line('{} = object()'.format(self.lang.format_class(field.name)))
                elif is_composite_type(field.data_type):
                    self.emit_line('{0} = {1}'.format(
                        self.lang.format_class(field.name),
                        self._class_name_for_data_type(field.data_type)))
                else:
                    raise ValueError('Only symbols and composite types for union fields.')
            self.emit_empty_line()

            self._generate_union_class_init(data_type)
            self._generate_union_class_from_json(data_type)
            self._generate_union_class_to_json(data_type)
            self._generate_union_class_repr(data_type)

    def _generate_union_class_init(self, data_type):
        """Generates the __init__ method for the class."""
        self.emit_line('def __init__', trailing_newline=False)
        args = ['self']
        for field in data_type.fields:
            args.append('{}=None'.format(field.name))
        args.append('**kwargs')
        self._generate_func_arg_list(args, compact=True)
        self.emit(':')
        self.emit_empty_line()

        with self.indent():
            self._generate_docstring_for_func(
                data_type,
                overview='Only one argument can be set.',
            )
            if data_type.fields:
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
                        assert_type = ("assert isinstance({0}, {1}), '{0} must be of type {1}'"
                            .format(
                                field.name,
                                self._is_instance_type(field.data_type)))
                    else:
                        assert_type = ("assert isinstance({0}, {1}), '{0} must be of type {2}'"
                            .format(
                                field.name,
                                'bool',
                                'bool'))
                    self.emit_line('if {} is not None:'.format(field.name))
                    with self.indent():
                        self.emit_line(assert_type)
                        self.emit_line('self.{0} = {0}'.format(field.name))
                        self.emit_line("self._tag = '{}'".format(field.name))
                    self.emit_empty_line()
            else:
                self.emit_line('pass')
                self.emit_empty_line()

        if data_type.fields:
            for field in data_type.fields:
                self.emit_line('def is_{}(self):'.format(self.lang.format_method(field.name)))
                with self.indent():
                    self.emit_line("return self._tag == '{}'".format(field.name))
                self.emit_empty_line()

    def _generate_union_class_from_json(self, data_type):
        """The from_json() function will convert a Python dictionary object
        that presumably was constructed from JSON into a Python object
        of the correct type."""
        self.emit_line('@classmethod')
        self.emit_line('def from_json(self, obj):')
        with self.indent():
            if data_type.all_fields:
                self.emit_line('obj = copy.copy(obj)')
            self.emit_line("assert len(obj) == 1, 'One key must be set, not %d' % len(obj)")
            for field in data_type.all_fields:
                if isinstance(field, SymbolField):
                    self.emit_line("if obj == '{}':".format(field.name))
                    with self.indent():
                        self.emit_line('return obj')
                elif is_composite_type(field.data_type):
                    self.emit_line("if '{}' in obj:".format(field.name))
                    with self.indent():
                        composite_assignment = "obj['{0}'] = {1}.from_json(obj['{0}'])".format(
                            field.name,
                            self._class_name_for_data_type(field.data_type),
                        )
                        self.emit_line(composite_assignment)
                else:
                    raise ValueError('Did not recognize field %r', field)
            self.emit_line('return {}(**obj)'.format(self._class_name_for_data_type(data_type)))
            self.emit_empty_line()

    def _generate_union_class_to_json(self, data_type):
        """The to_json() function will convert a Python object into a
        dictionary that can be serialized into JSON."""
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

    def _generate_union_class_repr(self, data_type):
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

    def _is_download_style(self, route):
        """If a route has Binary specified as the second segment of a request or response,
        the payload will be in the HTTP body. Binary should never appear anywhere else in a
        segmentation."""
        return route.attrs.get('style') == 'download'

    #
    # Routes
    #

    def _generate_route(self, namespace, route):
        """Generates Python methods that correspond to a route. We always generate a
        canonical method, which returns a Python object as a response. For download
        endpoints, we generate an endpoint that saves the contents into a file
        specified by the user."""
        self._generate_route_canonical(namespace, route)

        if self._is_download_style(route):
            self._generate_route_download_to_file(namespace, route)

    def _generate_route_canonical(self, namespace, route):
        """Generate a Python method that corresponds to an route."""
        request_data_type = route.request_data_type
        response_data_type = route.response_data_type

        host = self._generate_route_host(route.attrs.get('host', 'api'))
        style = self._generate_route_style(route.attrs.get('style', 'rpc'))
        request_binary_body = route.attrs.get('style') == 'upload'
        response_binary_body = route.attrs.get('style') == 'download'

        self._generate_route_method_decl(route, request_data_type, request_binary_body)

        with self.indent():
            extra_request_args = None
            extra_return_arg = None
            if request_binary_body:
                extra_request_args = [('f', None, 'A string or file-like obj of data.')]
            if response_binary_body:
                extra_return_arg = ':class:`requests.models.Response`'

            self._generate_docstring_for_func(
                request_data_type,
                response_data_type,
                route.error_data_type,
                overview=self.docf(route.doc),
                extra_request_args=extra_request_args,
                extra_return_arg=extra_return_arg,
            )

            if not is_null_type(request_data_type):
                # Code to instantiate a class for the request data type
                self.emit_line('o = {}'.format(
                    self._class_name_for_data_type(request_data_type)
                ), trailing_newline=False)
                self._generate_func_arg_list([f.name for f in request_data_type.all_fields])
                self.emit('.to_json()')
                self.emit_empty_line()
            else:
                self.emit_line('o = None')

            # Code to make the request
            self.emit_line('r = self._dropbox.request', trailing_newline=False)
            args = [host,
                    "'{}/{}'".format(namespace.name, route.path),
                    style,
                    'o']
            if request_binary_body:
                args.append('f')
            else:
                args.append('None')
            self._generate_func_arg_list(args, compact=True)
            self.emit_empty_line()

            return_args = []
            self.emit_line('return ', trailing_newline=False)
            if is_null_type(response_data_type):
                return_args.append('None')
            else:
                return_args.append('{}.from_json(r.obj_segment)'.format(
                    self._class_name_for_data_type(response_data_type)
                ))
            if response_binary_body:
                return_args.append('r.binary_segment')
            if len(return_args) == 1:
                self.emit(return_args[0])
            else:
                self._generate_func_arg_list(return_args)
            self.emit_empty_line()
        self.emit_empty_line()

    def _generate_route_download_to_file(self, namespace, route):
        """Generate a Python method that corresponds to a route. This should only be called
        for routes that return binary data. The method will take a path that will it use to
        save the binary data to."""
        request_data_type = route.request_data_type
        response_data_type = route.response_data_type

        host = self._generate_route_host(route.attrs.get('host', 'api'))
        style = self._generate_route_style(route.attrs.get('style', 'rpc'))
        request_binary_body = route.attrs.get('style') == 'upload'
        response_binary_body = route.attrs.get('style') == 'download'

        self._generate_route_method_decl(route,
                                         request_data_type,
                                         request_binary_body,
                                         method_name_suffix='_to_file',
                                         extra_args=['download_path'])

        with self.indent():
            extra_request_args = None
            if response_binary_body:
                extra_request_args = [
                    ('download_path', 'str', 'Path on local machine to save file.')]
            self._generate_docstring_for_func(
                request_data_type,
                response_data_type,
                route.error_data_type,
                overview=self.docf(route.doc),
                extra_request_args=extra_request_args,
            )

            if not is_null_type(request_data_type):
                # Code to instantiate a class for the request data type
                self.emit_line('o = {}'.format(
                    self._class_name_for_data_type(request_data_type)
                ), trailing_newline=False)
                self._generate_func_arg_list([f.name for f in request_data_type.all_fields])
                self.emit('.to_json()')
                self.emit_empty_line()
            else:
                self.emit_line('o = None')

            # Code to make the request
            self.emit_line('r = self._dropbox.request', trailing_newline=False)
            args = [host,
                    "'{}/{}'".format(namespace.name, route.path),
                    style,
                    'o']
            if request_binary_body:
                args.append('f')
            else:
                args.append('None')
            self._generate_func_arg_list(args, compact=True)
            self.emit_empty_line()

            self.emit_line("with open(download_path, 'w') as f:")
            with self.indent():
                self.emit_line('for c in r.binary_segment.iter_content(2**16):')
                with self.indent():
                    self.emit_line('f.write(c)')

            return_args = []
            self.emit_line('return ', trailing_newline=False)
            if is_null_type(response_data_type):
                return_args.append('None')
            else:
                return_args.append('{}.from_json(r.obj_segment)'.format(
                    self._class_name_for_data_type(response_data_type)
                ))
            self.emit(return_args[0])
            self.emit_empty_line()
        self.emit_empty_line()

    def _generate_route_host(self, host):
        """"Convert the host specified in the spec to the appropriate Python object."""
        if host == 'content':
            return 'Dropbox.Host.API_CONTENT'
        elif host == 'notify':
            return 'Dropbox.Host.API_NOTIFY'
        elif host == 'api':
            return 'Dropbox.Host.API'
        else:
            raise ValueError('Unknown host')

    def _generate_route_style(self, style):
        """"Convert the style specified in the spec to the appropriate Python object."""
        if style == 'rpc':
            return 'Dropbox.RouteStyle.RPC'
        elif style == 'download':
            return 'Dropbox.RouteStyle.DOWNLOAD'
        elif style == 'upload':
            return 'Dropbox.RouteStyle.UPLOAD'
        else:
            raise ValueError('Unknown route style')

    def _generate_route_method_decl(self, route, request_data_type, request_binary_body,
                                    method_name_suffix=None, extra_args=None):
        """Generates the method prototype for a route."""
        method_name = self.lang.format_method(route.name)
        if method_name_suffix:
            method_name += method_name_suffix
        self.emit_line('def {}'.format(method_name), trailing_newline=False)
        args = ['self']
        if extra_args:
            args += extra_args
        if request_binary_body:
            args.append('f')
        if not is_null_type(request_data_type):
            for field in request_data_type.all_fields:
                if field.optional or field.nullable:
                    if field.has_default:
                        arg = '{}={}'.format(field.name, self.lang.format_obj(field.default))
                        args.append(arg)
                    else:
                        args.append('{}=None'.format(field.name))
                else:
                    args.append(field.name)
        self._generate_func_arg_list(args)
        self.emit(':')
        self.emit_empty_line()
