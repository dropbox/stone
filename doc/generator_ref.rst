*******************
Generator Reference
*******************

Generators are a way to convert a spec into some other form. Most commonly,
a generator will target a programming language and convert a spec into
classes and functions.

All generators must be written as Python modules that satisfy the following
conditions:

1. The filename must have ``.babelg.py`` as its extension. For example,
   ``example.babelg.py``

2. At least one class must exist in the module that extends the
   ``babelapi.generator.generator.CodeGenerator`` class and implements the
   abstract ``generate()`` method. BabelAPI automatically detects subclasses
   and calls the ``generate()`` method. All such subclasses will be called in
   ASCII order.

Here's a simple no-op generator::

    from babelapi.generator.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self):
            pass

.. api-obj:

Using the API Object
====================

Code generators have a ``self.api`` member variable, which represents the input
specs as a Python object. The object is an instance of the ``babelapi.api.Api``
class. From this object, you can access all the defined namespaces, data types,
and routes.

Here's an example generator that creates no file output, but will print the
``api`` object to standard out::

    from babelapi.generator.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self):
            print self.api

See the Python object definition for more information.

.. create-output:

Creating an Output File
=======================

To create an output file, use the ``self.output_to_relative_path()`` function.
Its only argument is the path relative to the output directory, which was
specified as an argument to ``babelapi``, where the file should be created.

Here's an example generator that creates an empty output file ``empty.out``::

    from babelapi.generator.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self):
            with self.output_to_relative_path('empty.out'):
                pass

.. _emit_methods:

Emit*() Methods
===============

There are several ``emit*()`` methods that you can use from a ``CodeGenerator``
that each serve a different purpose.

``emit(s)``
    The input string is written to the output file.

``emit_line(s, trailing_newline=True)``
    The current indentation level followed by the input string is written to the
    output file. If ``trailing_newline`` is True (default) then a newline is
    written as well.

``emit_wrapped_lines(s, prefix='', width=80, trailing_newline=True, first_line_prefix=True)``
    The current indentation level followed by the input prefix (assuming
    ``first_line_prefix`` is ``True``) are written to the output file. The
    input string is then written into lines with each line starting with the
    indentation level and prefix. This is ideal for generating blocks of
    comments. Wrapping is done by words, and all trailing space in a line is
    truncated.

``emit_empty_line()``
    Writes an empty line to the output file.

``emit_indent()``
    Writes the number of spaces for the current indentation level to the output
    file.

.. indentation:

Indentation
===========

The ``babelapi.generator.generator.CodeGenerator`` class provides a context
manager for adding incremental indentation. Here's an example::

    from babelapi.generator.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self):
            with self.output_to_relative_path('ex_indent.out'):
                with self.indent()
                    self.emit_line('hello')
                    self._output_world()
        def _output_world(self):
            with self.indent():
                self.emit_line('world')

The contents of ``ex_indent.out`` is::

        hello
            world

Indentation is always four spaces. We plan to make this customizable in the
future.

.. examples:

Examples
========

The following examples can all be found in the ``babelapi/example/generator``
folder.

Example 1: List All Namespaces
------------------------------

We'll create a generator ``ex1.babelg.py`` that generates a file called
``ex1.out``. Each line in the file will be the name of a defined namespace::

    from babelapi.generator.generator import CodeGenerator

    class ExampleGenerator(CodeGenerator):
        def generate(self):
            """Generates a file that lists each namespace."""
            with self.output_to_relative_path('ex1.out'):
                for namespace in self.api.namespaces.values():
                    self.emit_line(namespace.name)

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

    from babelapi.generator.generator import CodeGenerator

    class ExamplePythonGenerator(CodeGenerator):
        def generate(self):
            """Generates a module for each namespace."""
            for namespace in self.api.namespaces.values():
                # One module per namespace is created. The module takes the name
                # of the namespace.
                with self.output_to_relative_path('{}.py'.format(namespace.name)):
                    self._generate_namespace_module(namespace)

        def _generate_namespace_module(self, namespace):
            self.emit_line('def noop():')
            with self.indent():
                self.emit_line('pass')

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

    from babelapi.data_type import Struct
    from babelapi.generator.generator import CodeGeneratorMonolingual
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

One new method of ``CodeGenerator`` that was used is ``generate_func_arg_list(args)``.
It helps you generate a list of arguments in a function declaration or invocation
enclosed by parentheses.
