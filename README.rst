****************
BabelAPI
****************

Define an API once in Babel. Implement or use an existing code generator to
map the API definition into usable objects and functions in any programming
language.

Motivation
==========

Being an API designer is tough. There are an innumerable number of protocols
and serialization formats that two hosts can use to communicate. Today, JSON
over HTTP is gaining popularity, but just a few years ago, XML was the
standard. To compound the issue, developers need to support an increasing
number of language-specific SDKs to gain wide adoption.

Babel seeks to:

    1. Define API endpoints in terms of input and output data types that can
       be consistently implemented in different protocols and languages.
    2. Use structs (product types) and tagged unions (sum types) as fundamental
       data types for modeling APIs flexibly, but strictly.
    3. Improve the visibility teams have into their APIs by centralizing
       specifications and documentation.

If we only had one protocol and one language BabelAPI wouldn't be needed, but
unfortunately humanity was handicapped for good reason. See
`Why do we have multiple programming languages?`_

Assumptions
-----------

Babel makes no assumptions about the protocol layer being used to make API
requests and return responses; its first use case is the Dropbox v2 API which
operates over HTTP. Babel does not come with nor enforces any particular RPC
framework.

Babel make some assumptions about the data types supported in the serialization
format and target programming language. It's assumed that there is a capacity
for representing dictionaries (unordered String Keys -> Value), lists, numeric
types, and strings. The intention is for Babel to map to a multitude of
serialization formats from JSON to Protocol Buffers.

Babel assumes that a route (or API endpoint) can have its request and
response types defined without relation to each other. In other words, the
type of response does not change based on the input to the endpoint. An
exception to this rule is afforded for error responses.

Getting Started
===============

Installation
------------

Download or clone BabelAPI, and run the following in its root directory::

   $ sudo python setup.py install

This will install a script ``babelapi`` to your PATH that can be run from the
command line::

   $ babelapi -h

If you did not run ``setup.py`` but have the Python package in your PYTHONPATH,
you can replace ``babelapi`` with ``python -m babelapi.cli`` as follows::

   $ python -m babelapi.cli -h

Simple Example
--------------

You can compile an example spec, ``users.babel`` describing the Dropbox API and
generate Python code using ``base_namespace.babelg.py``::

   $ babelapi example/generator/dropbox-python-sdk/dbx_python_json.babelg.py example/api/dbx-core/users.babel output/

You can view the generated code at::

   $ output/base_users.py

File Types
==========

There are three types of files.

Spec (.babel extension)
------------------------

Specifications define the data types and routes available in an API.

Header (.babelh extension)
--------------------------------

Headers define only data types available in an API. Headers can be included
in spec files so that common data types can be re-used.

Code Generator (.babelg.py extension)
--------------------------------------

Code generators are Python modules that implement the abstract
``babelapi.generator.generator.CodeGenerator`` class. BabelAPI automatically
detects subclasses and calls the ``generate()`` method. The code generator
has access to a ``self.api`` member variable which represents the spec as a
Python object.

Defining a Spec
===============

A spec is composed of a namespace followed by zero or more includes and zero or more definitions::

   Spec ::= Namespace Include* Definition*

Namespace
---------

Specs must begin with a namespace declaration::

   Namespace ::= 'namespace' Identifier

Example::

   namespace users

This is the namespace for all the routes and data types in the Spec file. It
helps us separate different logical groups of the API. For example, the Dropbox
API has a namespace devoted to all file operations (uploading, downloading, ...),
and another namespace for all operations relevant to user accounts.

Include
-------

Use an include to make all definitions in a Header available::

   Include ::= 'include' Identifier

Example::

   include common

This will search for a file called ``common.babelh`` in the same directory
as the Spec.

Definition
----------

There are four types of definitions available::

   Definition ::= Alias | Route | Struct | Union

Struct
------

A struct is a type made up of other types::

   struct Space
       "The space quota info for a user.

       This can be multi-line."

       quota UInt64
           "The user's total quota allocation (bytes)."
       private UInt64
           "The user's used quota outside of shared folders (bytes)."
       shared UInt64
           "The user's used quota in shared folders (bytes)."

       example default
           quota=1000000
           private=1000
           shared=500

A struct can be documented by specifying a string immediately following the
struct declaration. The string can be multiple lines, as long as each
subsequent line is at least at the indentation of the starting quote.

After the documentation is a list of fields. Fields are formatted with the field
name first followed by the field type. To provide documentation for a field,
specify a string on a new indented line following the field declaration.

Finally, examples can be declared. An example is declared by using the ``example``
keyword followed by a label, and optionally text. By convention, "default" should
be used as the label name for an example that can be considered a good
representation of the general case for the type.

Type Composition
^^^^^^^^^^^^^^^^

Types can also be composed of other types::

   struct Team
       "Information relevant to a team."

       name String
           "The name of the team."

       example default
           name="Acme, Inc."

   struct AccountInfo
       "Information for a user's account."

       display_name String
           "The full name of a user."
       space Space
           "The user's quota."
       is_paired Boolean
           "Whether the user has a personal and business account."
       team Team|Null
           "If this paired account is a member of a team."

       example default "Paired account"
           display_name="Jon Snow"
           is_paired=true

       example unpaired "Unpaired account"
           display_name="Jon Snow"
           is_paired=false
           team=null

Optionality
^^^^^^^^^^^

Note in the preceding example that the ``AccountInfo.team`` field has a data
type of ``Team`` followed by ``?``. ``?`` indicates that the field is optional.
To specify that the field is absent, you can use ``null`` in the example
definitions. By default, fields do not accept ``null`` as a valid value unless
the field is marked optional.

Type Inheritance
^^^^^^^^^^^^^^^^

A struct can also inherit from another struct using the ``extends`` keyword::

    struct EntryInfo
        "A file or folder entry."

        id String(max_length=40)
            "A unique identifier for the file."
        path String
            "Path to file or folder."
        modified DbxTimestamp|Null
            "The last time the file was modified on Dropbox, in the standard date
            format (null for root folder)."
        is_deleted Boolean
            "Whether the given entry is deleted."

    struct FileInfo extends EntryInfo
        "Describes a file."

        size UInt64
            "File size in bytes."
        mime_type String|Null
            "The Internet media type determined by the file extension."
        media_info MediaInfo?
            "Information specific to photo and video media."

        example default
            id="xyz123"
            path="/Photos/flower.jpg"
            size=1234
            mime_type="image/jpg"
            modified="Sat, 28 Jun 2014 18:23:21"
            is_deleted=false

Default Values
^^^^^^^^^^^^^^

The setting of default values for fields is best seen in the context of routes.
Please see the example below default_value_example_.

Union
-----

A union in Babel is a tagged union. In its field declarations, a tag name is followed by
a data type::

   struct PhotoInfo
       "Photo-specific information derived from EXIF data."

       time_taken DbxTimestamp
           "When the photo was taken."
       lat_long List(data_type=Float32)|Null
           "The GPS coordinates where the photo was taken."

       example default
           time_taken="Sat, 28 Jun 2014 18:23:21"
           lat_long=null

   struct VideoInfo
       "Video-specific information derived from EXIF data."

       time_taken DbxTimestamp
           "When the photo was taken."
       lat_long List(data_type=Float32)|Null
           "The GPS coordinates where the photo was taken."
       duration Float32
           "Length of video in milliseconds."

       example default
           time_taken="Sat, 28 Jun 2014 18:23:21"
           lat_long=null
           duration=3

   union MediaInfo
       "Media specific information."

       photo PhotoInfo
       video VideoInfo

Tags can be declared without mapping to a type. We call these Symbols. The
following example illustrates::

    union WriteConflictPolicy
        "Policy for managing write conflicts."

        reject
            "On a write conflict, reject the new file."
        overwrite
            "On a write conflict, overwrite the existing file."
        rename
            "On a write conflict, rename the new file with a numerical suffix."

Catch All Symbol
^^^^^^^^^^^^^^^^

By default, we consider Unions to be closed. That is, for the sake of backwards
compatibility, a client should never receive a variant that it isn't aware of.
Therefore, expanding a union requires writing a new route and a new Union with
the additional variant.

Because we anticipate that this will be a hassle for APIs undergoing revision,
we've introduced a notation to indicate that in the event a tag is not known,
the union will default to a symbol. The notation is simply an asterix that
follows a symbol field name::

    union GetAccountError
        no_account
            "No account could be found."
        unknown*

In the example above, a client that received a tag it did not understand
(e.g. ``permission_denied``) will default to the ``unknown`` tag.

We expect this to be especially useful for unions that represent the possible
errors an endpoint might return. Clients in the wild may have been generated
with only a subset of the current errors, but they'll continue to function as
long as they handle the catch all tag.

Any Data Type
^^^^^^^^^^^^^

Changing a symbol field to some data type is a backwards incompatible change
that requires creating a new route and union definition. After all, if a
client is expecting a symbol and gets back a struct, it isn't likely the
handling code will be prepared.

To avoid this, set the field to the ``Any`` data type::

    union GetAccountError
        no_account Any
            "No account could be found."

Now, without rev-ing the route, it will be possible to change the definition
in the future without breaking old clients::

    union GetAccountError
        no_account MoreInfoStruct
            "No account could be found."

Primitives
----------

These types exist without having to be declared:

   * Boolean
   * Integers: Int32, Int64, UInt32, UInt64
      * Attributes ``min_value`` and ``max_value`` can be set for more
        restrictive bounding.
   * Float32, Float64
   * String
      * Attributes ``min_length`` and ``max_length`` can be set.
   * Timestamp
      * The ``format`` attribute must be set to define the format of the
        timestamp.
   * List
      * The ``data_type`` must be set to define the type of elements.

Alias
-----

Sometimes we prefer to use an alias, rather than re-declaring a type over and over again.
For example, the Dropbox API uses a special date format. We can create an alias called
DbxTimestamp, which sets this format, and can be used in struct and union definitions::

   alias DbxTimestamp = Timestamp(format="%a, %d %b %Y %H:%M:%S")

   struct Example
       "An example."

       created DbxTimestamp
           "When this example was created."

Routes
------

Routes map to your API endpoints. You specify data types that represent the
input and output of a request. An optional third argument is a data type for
representing errors that may be returned::

    struct AccountInfoRequest
        "Input to request."

        account_id String = "me"
            "A user's account identifier. Use "me" to get information for the
            current account."

    union AccountInfoError
        no_account
            "If the requested account could not be found"
        no_access
            "Information cannot be retrieved due to access permissions"

    route GetInfo (AccountInfoRequest, AccountInfo, AccountInfoError)
        "Get user account information"

.. _default_value_example:

Note that ``account_id`` was given a default value of ``"me"``. This is useful
for including in generated SDKs.

A full description of an API route tends to require vocabulary that is specific
to a service. For example, the Dropbox API needs a way to specify some routes
as including a binary body (uploads) for requests. Another example is specifying
some routes as requiring authentication while others do not.

To cover this open ended use case, routes can have an ``attrs`` section declared
followed by an arbitrary set of ``key=value`` pairs::

    struct FileUploadRequest
        path String
            "The full path to the file you want to write to. It should not point
            to a folder."

    route Upload (FileUploadRequest, FileInfo)
        "Upload a file to Dropbox."

        attrs
            style="upload"

The code generator we've written for our API will check a route's ``style``
attribute and ensure that it constructs an HTTP request where the body is
the file contents. As an aside, we've chosen to encode the ``FileUploadRequest``
struct in a JSON-encoded header though others may prefer to encode it in query
parameters.

Documentation
-------------

To help template writers tailor documentation to a language, we support stubs
in documentation. Stubs are of the following format::

    :tag:`value`

Supported tags are ``route``, ``struct``, ``field``, ``link``, and ``val``.

route
    A reference to a route. Template writers should make a reference to
    the method that represents the route.
struct
    A reference to a struct. Template writers should make a reference to the
    class that represents the struct.
field
    A reference to a field of a struct. It's intended for referencing
    parameters for functions, but its utility is still TBD.
link
    A hyperlink. Template writers should convert this to the proper hyperlink
    format for the language.
val
    A value. Template writers should convert this to the native representation
    of the value for the language. For example, a ``None`` would be converted
    to ``null`` in Javascript.

Defining a Code Generator
=========================

A code generator is a Python class which will generate code for a target language
given an API description. A code generator must satisfy the following conditions:

1. The filename must have ``.babelg.py`` as its extension. For example,
   ``example.babelg.py``

2. A class must exist in the file that extends the
   ``babelapi.generator.generator.CodeGenerator`` class and implements the
   abstract ``generate()`` method. BabelAPI automatically detects subclasses
   and calls the ``generate()`` method.

Using the API Object
--------------------

Code generators have a ``self.api`` member variable. The object is an instance
of the ``babelapi.api.Api`` class. From this object, you can access all the
defined namespaces, data types, and routes. See the Python object definition
for more information.

Examples
--------

The following examples can all be found in the ``babelapi/example/generator``
folder.

Example 1: List All Namespaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

    $ babelapi example/api/dbx-core*.babel example/generator/ex1
    $ babelapi example/generator/ex1/ex1.babelg.py example/api/dbx-core/*.babel output/ex1

Now examine the contents of the output::

    $ cat example/generator/ex1/ex1.out
    files
    users

.. _emit_methods:

Emit*() Methods
^^^^^^^^^^^^^^^

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
    comments.

``emit_empty_line()``
    Writes an empty line to the output file.

``emit_indent()``
    Writes the number of tabs or spaces for the current indentation level to
    the output file.

Example 2: A Python module for each Namespace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Target SDKs
===========

* Python
* Objective-C/iOS
* Java/Android
* Ruby
* PHP

Other Targets
=============

* Web Docs
* Server Input Validation
* Server Output Validation

General Rules
=============

* Clients must accept new fields (ie. fields unknown to it), and ignore them.
* Server should be flexible on missing inputs (backwards compatibility) if a
  default value has been specified in the spec, but strict on what goes out.

.. _why_multiple_languages:

Why do we have multiple programming languages?
==============================================

From the King James version of the Bible:

    4 And they said, Go to, let us build us a city and a tower, whose top may reach unto heaven; and let us make us a name, lest we be scattered abroad upon the face of the whole earth.

    5 And the Lord came down to see the city and the tower, which the children of men builded.

    6 And the Lord said, Behold, the people is one, and they have all one language; and this they begin to do: and now nothing will be restrained from them, which they have imagined to do.

    7 Go to, let us go down, and there confound their language, that they may not understand one another's speech.

    8 So the Lord scattered them abroad from thence upon the face of all the earth: and they left off to build the city.

    9 Therefore is the name of it called Babel; because the Lord did there confound the language of all the earth: and from thence did the Lord scatter them abroad upon the face of all the earth.

    —Genesis 11:4–9[1]
