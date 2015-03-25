********************
Using Generated Code
********************

Using a generator, you can convert the structs, unions, and routes in your spec
into objects in your programming language of choice.

Currently, the only generator included with Babel is for `Python
<#python-guide>`_. We intend to create generators for an assortment of
languages including:

    * Java
    * Javascript
    * PHP
    * Ruby
    * Swift

If you're looking to make your own generator, see
`Writing a Generator <generator_ref.rst>`_.

Compile with the CLI
====================

Compiling a spec and generating code is done using the ``babelapi``
command-line interface (CLI)::

    $ babelapi -h
    usage: babelapi [-h] [-v] generator spec [spec ...] output

    BabelAPI

    positional arguments:
      generator      Specify the path to a generator. It must have a .babelg.py
                     extension.
      spec           Path to API specifications. Each must have a .babel
                     extension.
      output         The folder to save generated files to.

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Print debugging statements.

We'll compile the ``users.babel`` example from the
`Language Reference <lang_ref.rst>`_. The first argument is the path to the
Python generator which can be found in the ``babelapi`` folder::

    $ babelapi generator/python/python.babelg.py users.babel .
    INFO:babelapi.idl:Parsing spec users.babel
    INFO:babelapi.compiler:Found generator at ...
    INFO:babelapi.compiler:Running generator ...
    INFO:bablesdk.generator.PythonGenerator:Copying babel_validators.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Copying babel_serializers.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Generating ./users.py

The first argument selects the included Python code generator. ``users.babel``
is the spec file to compile. If we had another spec file, we could list it
right after ``users.babel``. The ``.`` says to save the output of the code
generator to the current directory.

Python Guide
============

This section explains how to use the pre-packaged Python generator and work
with the Python classes that have been generated from a spec.

From the above section, you can generate Python using::

    $ babelapi generator/python/python.babelg.py users.babel .

This runs the Python generator on the ``users.babel`` spec. Its output
target is ``.``, which is the current directory. A Python module is created for
each declared namespace, so in this case only ``users.py`` is created.

Two additional modules are copied into the target directory. The first,
``babel_validators.py``, contains classes for validating Python values against
their expected Babel types. You will not need to explicitly import this module,
but the auto-generated Python modules depend on it. The second,
``babel_serializers.py``, contains a ``json_encode()`` and ``json_decode()``
function. You will need to import this module to serialize your objects.

In the following sections, we'll interact with the classes generated in
``users.py``. For simplicity, we'll assume we've opened a Python interpreter
with the following shell command::

    $ python -i users.py

For non-test projects, we recommend that you set a generation target within a
Python package, and use Python's import facility.

Primitive Types
---------------

The following table shows the mapping between a Babel `primitive type
<lang_ref.rst#primitive-types>`_ and its corresponding type in Python.

========================== ============ =======================================
Primitive                  Python 2.x   Notes
========================== ============ =======================================
Binary                     str
Boolean                    bool
Float{32,64}               float        long type within range is converted.
Int{32,64}, UInt{32,64}    long
List                       list
String                     unicode      str type is converted to unicode.
Timestamp                  datetime
========================== ============ =======================================

Struct
------

For each struct in your spec, you will see a corresponding Python class of the
same name.

In our example, ``BasicAccount``, ``Account``, and ``GetAccountReq`` are all
Python classes. They have an attribute (getter/setter/deleter property) for
each field defined in the spec. You can instantiate these classes and specify
field values either in the constructor or by assigning to an attribute::

    >>> b = BasicAccount(account_id='id-48sa2f0')
    >>> b.email = 'alex@example.org'

If you assign a value that fails validation, an exception is raised::

    >>> b.email = 10
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "users.py", line 149, in email
        val = self.__email_data_type.validate(val)
      ...
    babel_data_types.ValidationError: '10' expected to be a string, got integer

    >>> b.email = 'bob'
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "users.py", line 149, in email
        val = self.__email_data_type.validate(val)
        ...
    babel_data_types.ValidationError: 'bob' did not match pattern '^[^@]+@[^@]+.[^@]+$'

Inheritance in Babel also shows up as inheritance in Python::

    >>> issubclass(Account, BasicAccount)
    True

Accessing a required field (non-optional with no default) that has not been set
raises an error::

    >>> a = Account()
    >>> a.account_id
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "users.py", line 58, in account_id
        raise AttributeError("missing required field 'account_id'")
    AttributeError: missing required field 'account_id'

If a field is optional and was never set, ``None`` is returned::

    >>> print a.name
    None

If a field has a default but was never set, the default is returned.

Union
-----

For each union in your spec, you will see a corresponding Python class of the
same name.

You do not use a union class's constructor directly. To select a tag with a
void type, use the class attribute of the same name::

    >>> GetAccountErr.no_account
    GetAccountErr('no_account')

To select a tag with a value, use the class method of the same name and pass
in an argument to serve as the value.

    >>> import datetime
    >>> Status.inactive(datetime.datetime.utcnow())
    Status('inactive')

The value is also validated on creation::

    >>> Status.inactive('bad value')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "users.py", line 121, in inactive
        return cls('inactive', val)
      ...
    babel_data_types.ValidationError: expected timestamp, got string

To write code that handles all the tags of a union, use the ``is_[tag]()``
methods. We recommend you exhaustively check all tags, or include an else
clause to ensure that all possibilities are accounted for. For tags that have
values, use the ``get_[tag]()`` method to access the value::

    >>> # assume that s is an instance of Status
    >>> if s.is_active():
    ...     # handle active status
    ... elif s.is_inactive():
    ...     v = s.get_inactive()
    ...     # handle inactive status

Route
-----

[TODO]
