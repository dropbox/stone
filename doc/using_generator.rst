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
      generator      Specify a pre-packaged generator (only "python" right now),
                     or the path to a custom generator (.babelg.py).
      spec           Path to API specifications (*.babel).
      output         The folder to save generated files to.

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Print debugging statements.

We'll compile the ``users.babel`` example from the
`Language Reference <lang_ref.rst>`_::

    $ babelapi python users.babel .
    INFO:babelapi.idl:Parsing spec users.babel
    INFO:babelapi.compiler:Found generator at ...
    INFO:babelapi.compiler:Running generator ...
    INFO:bablesdk.generator.PythonGenerator:Copying babel_data_types.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Copying babel_serializers.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Generating ./users.py

The first argument, ``python``, selects the included Python code generator.
``users.babel`` is the spec file to compile. If we had another spec file, we
could list it right after ``users.babel``. The ``.`` says to save the output
of the code generator to the current directory.

Python Guide
============

This section explains how to generate Python code and work with the Python
classes that have been generated from a spec.

From the above section, you can generate Python using::

    $ babelapi python users.babel .

This runs the ``python`` generator on the ``users.babel`` spec. Its output
target is ``.``, which means it will create a module called ``users.py`` in the
current directory.

In the following sections, we'll interact with the classes generated in
``users.py``. For simplicity, we'll assume we've opened a Python interpreter
with the following shell command::

    $ python -i users.py

We recommend that you place ``users.py`` in a Python package, and import it,
when using it in a non-test project.

Primitive Types
---------------

The following table shows the mapping between a Babel `primitive type
<lang_ref.rst#primitive-types>`_ and its corresponding type in Python.

============================= =======================
Primitive                     Python 2
============================= =======================
Binary                        str
Boolean                       bool
Float{32,64}                  float
Int{32,64}, UInt{32,64}       long
List                          list
String                        unicode
Timestamp                     datetime
============================= =======================

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

You do not use a union class's constructor directly. To select a symbol (or a
`Any data type <lang_ref.rst#union-any>`_) tag, use the class attribute of
the same name::

    >>> GetAccountErr.no_account # symbol
    GetAccountErr('no_account')
    >>> GetAccountErr.perm_denied # Any data type
    GetAccountErr('perm_denied')

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

Validation
----------

While structs and unions validate on assignment, that isn't sufficient for
comprehensive validation. For example, validating on assignment does not check
whether all required fields have been set.

To do comprehensive validation, you will need to import ``babel_validators.py``
which was dropped into the output folder of the Python generation by the Python
generator. It includes Python classes ``Struct`` and ``Union`` which can be
used for validation::

    >>> import babel_validators as bv
    >>> b_validator = bv.Struct(BasicAccount)
    >>> b = BasicAccount(account_id='id-48sa2f0')
    >>> b_validator.validate(b)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      ...
    babel_validators.ValidationError: missing required field 'email'

There is also a class for every Babel primitive type, each with a
``validate()`` method for validation::

    >>> bv.String().validate(42)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      ...
    babel_validators.ValidationError: '42' expected to be a string, got integer

Validators are especially important if you're considering looking to write a
serializer/deserializer for Babel. For example, our included JSON serializer
will validate all objects before converting them to their JSON representation.

Future work: Rather than dropping in ``babel_validators``, it could live in a
separate package that can be pip installed.

Route
-----

[TODO]
