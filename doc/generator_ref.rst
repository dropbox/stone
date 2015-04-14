*******************
Writing a Generator
*******************

This document explains how to write your own generator. If you're simply
looking to use an included generator, please see `Using Generated Code
<using_generator.rst>`_.

Generators convert a spec into some other markup or code. Most commonly, a
generator will target a programming language and convert a spec into classes
and functions. But, generators can also create markup for things like API
documentation.

Generators are written as Python modules that satisfy the following
conditions:

1. The filename must have a ``.babelg.py`` extension. For example,
   ``example.babelg.py``

2. At least one class must exist in the module that extends the
   ``babelapi.generator.CodeGenerator`` class and implements the abstract
   ``generate()`` method. BabelAPI automatically detects subclasses and calls
   the ``generate()`` method. All such subclasses will be called in ASCII
   order.

Getting Started
===============

Here's a simple no-op generator::

    from babelapi.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self, api):
            pass

Assuming that the generator is saved in your current directory as
``example.babelg.py`` and that our running example spec ``users.babel`` from the
`Language Reference <lang_ref.rst>`_ is also in the current directory. you can
invoke the generator with the following command::

    $ babelapi example.babelg.py users.babel .

Generating Output Files
=======================

To create an output file, use the ``output_to_relative_path()`` method.
Its only argument is the path relative to the output directory, which was
specified as an argument to ``babelapi``, where the file should be created.

Here's an example generator that creates an output file for each namespace.
Each file is named after a respective namespace and have a ``.cpp`` extension.
Each file contains a one line C++-style comment::

    from babelapi.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self, api):
            for namespace_name in api.namespaces:
                with self.output_to_relative_path(namespace_name + '.cpp'):
                    self.emit('/* {} */'.format(namespace_name))

Using the API Object
====================

The ``generate`` method receives an ``api`` variable, which represents the API
spec as a Python object. The object is an instance of the ``babelapi.api.Api``
class. From this object, you can access all the defined namespaces, data types,
and routes.

Api
---

namespaces
    A map from namespace name to Namespace object.


Namespace
---------

name
    The name of the namespace.

routes
    A list of Route objects in the order that they were defined.

route_by_name
    A map from route name to Route object.

data_types
    A list of user-defined DataType objects in the order that they were
    defined.

data_type_by_name
    A map from data type name to DataType object.

distinct_route_io_data_types()
    A set of all user-defined data types that are referenced as either a
    request, response, or error data type of a route. If a route has a List
    data type, then the contained data type is returned if it's a user-defined
    type.

Route
-----

name
    The name of the route.

doc
    The documentation string for the route.

request_data_type
    A DataType object of a request.

response_data_type
    A DataType object of a response.

error_data_type
    A DataType object of an error.

attrs
    A map from string keys to Python primitive values that is a direct copy
    of the attrs specified in the route definition.

See the Python object definition for more information.

DataType
--------

name
    The name of the data type.

nullable
    Whether the type is nullable.

See ``babelapi.data_type`` for all primitive type definitions and their
attributes.

Struct
------

name
    The name of the struct.

doc
    The documentation string for the struct.

all_fields
    A list of all StructField objects that make up the struct. Required fields
    come before optional fields.

supertype
    If it exists, it points to a DataType object (another struct) that this
    struct inherits from.

StructField
-----------

name
    The name of the field.

doc
    The documentation string for the field.

data_type
    The DataType of the field.

Union
-----

[TODO]: Need to rename fields to tags first.

.. _emit_methods:

Emit*() Methods
===============

There are several ``emit*()`` methods included in a ``CodeGenerator`` that each
serve a different purpose.

``emit(s='')``
    Adds indentation, then the input string, and lastly a newline to the output
    buffer. If ``s`` is an empty string (default) then an empty line is created
    with no indentation.

``emit_wrapped_text(s, prefix='', initial_prefix='', subsequent_prefix='', width=80, break_long_words=False, break_on_hyphens=False)``
    Adds the input string to the output buffer with indentation and wrapping.
    The wrapping is performed by the ``textwrap.fill`` Python library
    function.

    ``prefix`` is prepended to every line of the wrapped string.
    ``initial_prefix`` is prepended to the first line of the wrapped string
    ``subsequent_prefix`` is prepended to every line after the first.
    On a line, ``prefix`` will always come before ``initial_prefix`` and
    ``subsequent_prefix``. ``width`` is the target width of each line including
    indentation and prefixes.

    If true, ``break_long_words`` breaks words longer than width.  If false,
    those words will not be broken, and some lines might be longer
    than width. If true, ``break_on_hyphens`` allows breaking hyphenated words;
    wrapping will occur preferably on whitespaces and right after the hyphen
    in compound words.

``emit_raw(s)``
    Adds the input string to the output buffer. The string must end in a
    newline. It may contain any number of newline characters. No indentation is
    generated.

Indentation
===========

The ``babelapi.generator.CodeGenerator`` class provides a context
manager for adding incremental indentation. Here's an example::

    from babelapi.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self, api):
            with self.output_to_relative_path('ex_indent.out'):
                with self.indent()
                    self.emit('hello')
                    self._output_world()
        def _output_world(self):
            with self.indent():
                self.emit('world')

The contents of ``ex_indent.out`` is::

        hello
            world

Indentation is always four spaces. We plan to make this customizable in the
future.

Helpers for Code Generation
===========================

``generate_multiline_list(items, before='', after='', delim=('(', ')'), compact=True, sep=',', skip_last_sep=False)``
    Given a list of items, emits one item per line. This is convenient for
    function prototypes and invocations, as well as for instantiating arrays,
    sets, and maps in some languages.

    ``items`` is the list of strings that make up the list. ``before`` is the
    string that comes before the list of items. ``after`` is the string that
    follows the list of items. The first element of ``delim`` is added
    immediately following ``before``, and the second element is added
    prior to ``after``.

    If ``compact`` is true, the enclosing parentheses are on the same lines as
    the first and last list item.

    ``sep`` is the string that follows each list item when compact is true. If
    compact is false, the separator is omitted for the last item.
    ``skip_last_sep`` indicates whether the last line should have a trailing
    separator. This parameter only applies when ``compact`` is false.

``block(before='', after='', delim=('{','}'), dent=None, allman=False)``
    A context manager that emits configurable lines before and after an
    indented block of text. This is convenient for class and function
    definitions in some languages.

    ``before`` is the string to be output in the first line which is not
    indented. ``after`` is the string to be output in the last line which is
    also not indented. The first element of ``delim`` is added immediately
    following ``before`` and a space. The second element is added prior to a
    space and then ``after``. ``dent`` is the amount to indent the block. If
    none, the default indentation increment is used. ``allman`` indicates
    whether to use ``Allman`` style indentation instead of the default ``K&R``
    style.  For more about indent styles see `Wikipedia
    <http://en.wikipedia.org/wiki/Indent_style>`_.

``process_doc(doc, handler)``
    Helper for parsing documentation `references <lang_ref.rst#doc-refs>`_ in
    Babel docstrings and replacing them with more suitable annotations for the
    target language.

    ``doc`` is the docstring to scan for references. ``handler`` is a function
     you define with the following signature: `(tag: str, value: str) -> str`.
     ``handler`` will be called for every reference found in the docstring with
     the tag and value parsed for you. The returned string will be substituted
     in the docstring for the reference.

Generator Instance Variables
============================

logger
    This is an instance of the `logging.Logger
    <https://docs.python.org/2/library/logging.html#logger-objects>`_ class
    from the Python standard library. Messages written to the logger will be
    output to standard error as the generator runs.

target_folder_path
    The path to the output folder. Use this when the
    ``output_to_relative_path`` method is insufficient for your purposes.

Data Type Classification Helpers
================================

``babelapi.data_type`` includes functions for classifying data types. These are
useful when generators need to discriminate between types. The following are
available::

    is_binary_type(data_type)
    is_boolean_type(data_type)
    is_composite_type(data_type)
    is_integer_type(data_type)
    is_empty(data_type)
    is_float_type(data_type)
    is_list_type(data_type)
    is_numeric_type(data_type)
    is_primitive_type(data_type)
    is_string_type(data_type)
    is_struct_type(data_type)
    is_tag_ref(val)
    is_timestamp_type(data_type)
    is_union_type(data_type)
    is_void_type(data_type)

Examples
========

The following examples can all be found in the ``babelapi/example/generator``
folder.

Example 1: List All Namespaces
------------------------------

We'll create a generator ``ex1.babelg.py`` that generates a file called
``ex1.out``. Each line in the file will be the name of a defined namespace::

    from babelapi.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self, api):
            """Generates a file that lists each namespace."""
            with self.output_to_relative_path('ex1.out'):
                for namespace in api.namespaces.values():
                    self.emit(namespace.name)

We use ``output_to_relative_path()`` a member of ``CodeGenerator`` to specify
where the output of our ``emit*()`` calls go (See more emit_methods_).

Run the generator from the root of the BabelAPI folder using the example specs
we've provided::

    $ babelapi example/generator/ex1/ex1.babelg.py example/api/dbx-core/*.babel output/ex1

Now examine the contents of the output::

    $ cat example/generator/ex1/ex1.out
    files
    users

Example 2: A Python module for each Namespace
---------------------------------------------

Now we'll create a Python module for each namespace. Each module will define
a ``noop()`` function::

    from babelapi.generator import CodeGenerator

    class ExamplePythonGenerator(CodeGenerator):
        def generate(self, api):
            """Generates a module for each namespace."""
            for namespace in api.namespaces.values():
                # One module per namespace is created. The module takes the name
                # of the namespace.
                with self.output_to_relative_path('{}.py'.format(namespace.name)):
                    self._generate_namespace_module(namespace)

        def _generate_namespace_module(self, namespace):
            self.emit('def noop():')
            with self.indent():
                self.emit('pass')

Note how we used the ``self.indent()`` context manager to increase the
indentation level by a default 4 spaces. If you want to use tabs instead,
set the ``tabs_for_indents`` class variable of your extended CodeGenerator
class to ``True``.

Run the generator from the root of the BabelAPI folder using the example specs
we've provided::

    $ babelapi example/generator/ex2/ex2.babelg.py example/api/dbx-core/*.babel output/ex2

Now examine the contents of the output::

    $ cat output/ex2/files.py
    def noop():
        pass
    $ cat output/ex2/users.py
    def noop():
        pass

Example 3: Define Python Classes for Structs
--------------------------------------------

As a more advanced example, we'll define a generator that makes a Python class
for each struct in our specification. We'll extend from
``MonolingualCodeGenerator``, which enforces that a ``lang`` class variable is
declared::

    from babelapi.data_type import is_struct_type
    from babelapi.generator import CodeGeneratorMonolingual
    from babelapi.lang.python import PythonTargetLanguage

    class ExamplePythonGenerator(CodeGeneratorMonolingual):

        # PythonTargetLanguage has helper methods for formatting class, obj
        # and variable names (some languages use underscores to separate words,
        # others use camelcase).
        lang = PythonTargetLanguage()

        def generate(self, api):
            """Generates a module for each namespace."""
            for namespace in api.namespaces.values():
                # One module per namespace is created. The module takes the name
                # of the namespace.
                with self.output_to_relative_path('{}.py'.format(namespace.name)):
                    self._generate_namespace_module(namespace)

        def _generate_namespace_module(self, namespace):
            for data_type in namespace.linearize_data_types():
                if not is_struct_type(data_type):
                    # Only handle user-defined structs (avoid unions and primitives)
                    continue

                # Define a class for each struct
                class_def = 'class {}(object):'.format(self.lang.format_class(data_type.name))
                self.emit(class_def)

                with self.indent():
                    if data_type.doc:
                        self.emit('"""')
                        self.emit_wrapped_text(data_type.doc)
                        self.emit('"""')

                    self.emit()

                    # Define constructor to take each field
                    args = ['self']
                    for field in data_type.fields:
                        args.append(self.lang.format_variable(field.name))
                    self.generate_multiline_list(args, 'def __init__', ':')

                    with self.indent():
                        if data_type.fields:
                            self.emit()
                            # Body of init should assign all init vars
                            for field in data_type.fields:
                                if field.doc:
                                    self.emit_wrapped_text(field.doc, '# ', '# ')
                                member_name = self.lang.format_variable(field.name)
                                self.emit('self.{0} = {0}'.format(member_name))
                        else:
                            self.emit('pass')
                self.emit()
