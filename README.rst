****************
BabelAPI
****************

Define an API once in Babel. Implement or use an existing code generator to
map the API definition into usable objects and functions in any programming
language.

Babel makes no assumptions about the protocol layer being used to make API
requests and return responses; its first use case is the Dropbox v2 API which
operates over HTTP. Babel does not come with nor enforces any particular RPC
framework.

Babel make some assumptions about the data types supported in the serialization
format and target programming language. It's assumed that there is a capacity
for representing dictionaries (unordered String Keys -> Value), lists, numeric
types, and strings. The intention is for Babel to map to a multitude of
serialization formats from JSON to Protocol Buffers.

Babel assumes that an operation (or API endpoint) can have its request and
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

You can compile an example babel and apply it to a documentation template::

   $ babelapi example/api/v2_files.babel example/api/v2_users.babel example/template/docs

You can view the generated documentation using::

   $ google-chrome example/template/docs/docs.html

Fundamentals
============

There are three types of files.

Spec (.babel extension)
------------------------

Specifications define the data types and operations available in an API.

Header (.babelh extension)
--------------------------------

Headers define only data types available in an API. Headers can be included
in spec files so that common data types can be re-used.

Code Generator (.babelt.py extension)
--------------------------------------

Code generators are Python modules that implement the abstract
``babelapi.generator.generator.CodeGenerator`` class. BabelAPI automatically
detects subclasses and calls the ``generate()`` method. The code generator
has access to a ``self.api`` member variable which represents the spec as a
Python object.

Defining a Spec
================

A spec is composed of a namespace followed by zero or more includes and zero or more definitions::

   Spec ::= Namespace Include* Definition*

Namespace
---------

Specs must begin with a namespace declaration::

   Namespace ::= 'namespace' Identifier

Example::

   namespace users

This is the namespace for all the operations and data types in the Spec file. It
helps us separate different parts of the API like "files", "users", and "photos".

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

   Definition ::= Alias | Struct | Union | Operation

Struct
------

A struct is a type made up of other types::

   struct Space
       doc:
           The space quota info for a user.

       quota UInt64:
           The user's total quota allocation (bytes).
       private UInt64:
           The user's used quota outside of shared folders (bytes).
       shared UInt64:
           The user's used quota in shared folders (bytes).

       example default
           quota=1000000
           private=1000
           shared=500

A struct can optionally define a documentation string by declaring ``doc:``.
The colon enters documentation mode and indicates that the following
text is free form. Documentation mode is terminated only by a line that has the
same indentation as the original "doc:" string.

After the documentation is a list of fields. Fields are formatted with the field
name first followed by the field type. To provide documentation for a field, use
``:`` again,otherwise end the line with the field type.

Finally, examples can be declared. An example is declared by using the ``example``
keyword followed by a label, and optionally text. By convention, "default" should
be used as the label name for an example that can be considered a good
representation of the general case for the type.

Type Composition
^^^^^^^^^^^^^^^^

Types can also be composed of other types::

   struct Team
       doc:
           Information relevant to a team.

       name String:
           The name of the team.

       example default
           name="Acme, Inc."

   struct AccountInfo:
       doc:
           Information for a user's account.

       display_name String:
           The full name of a user.
       space Space:
           The user's quota.
       is_paired Boolean:
           Whether the user has a personal and business account.
       team Team|Null:
           If this paired account is a member of a team.

       example default "Paired account"
           display_name="Jon Snow"
           is_paired=true

       example unpaired "Unpaired account"
           display_name="Jon Snow"
           is_paired=false
           team=null


Nullability
^^^^^^^^^^^

Note in the preceding example that the ``AccountInfo.team`` field can be a
``Team`` struct or ``Null``. By default, fields do not accept ``null`` as a
valid value unless explicitly indicated.

Type Inheritance
^^^^^^^^^^^^^^^^

A struct can also inherit from another struct using the ``extends`` keyword::

    struct EntryInfo:
        doc::
            A file or folder entry.

        id String(max_length=40)::
            A unique identifier for the file.
        path String::
            Path to file or folder.
        modified DbxTimestamp|Null::
            The last time the file was modified on Dropbox, in the standard date
            format (null for root folder).
        is_deleted Boolean::
            Whether the given entry is deleted.

    struct FileInfo extends EntryInfo:
        doc::
            Describes a file.

        size UInt64::
            File size in bytes.
        mime_type String|Null::
            The Internet media type determined by the file extension.
        media_info MediaInfo optional::
            Information specific to photo and video media.

        example default:
            id="xyz123"
            path="/Photos/flower.jpg"
            size=1234
            mime_type="image/jpg"
            modified="Sat, 28 Jun 2014 18:23:21"
            is_deleted=false

Optional Fields
^^^^^^^^^^^^^^^
Note in the preceding example the use of the ``optional`` keyword which denotes
that the field may not be present. We do not conflate the optionality of a field
with the nullability of a field's data_type. However, these concepts may be
intentionally conflated in languages that don't maintain a strict difference.

Default Values
^^^^^^^^^^^^^^

The setting of default values for fields is best seen in the context of operations.
Please see the example below default_value_example_.

Union
-----

A union in Babel is a tagged union. In its field declarations, a tag name is followed by
a data type::

   struct PhotoInfo:
       doc::
           Photo-specific information derived from EXIF data.

       time_taken DbxTimestamp::
           When the photo was taken.
       lat_long List(data_type=Float32)|null::
           The GPS coordinates where the photo was taken.

       example default:
           time_taken="Sat, 28 Jun 2014 18:23:21"
           lat_long=null

   struct VideoInfo:
       doc::
           Video-specific information derived from EXIF data.

       time_taken DbxTimestamp::
           When the photo was taken.
       lat_long List(data_type=Float32)|null::
           The GPS coordinates where the photo was taken.
       duration Float32::
           Length of video in milliseconds.

       example default:
           time_taken="Sat, 28 Jun 2014 18:23:21"
           lat_long=null
           duration=3

   union MediaInfo:
       doc::
           Media specific information.

       photo PhotoInfo
       video VideoInfo

Tags that do not map to a type can be declared. The following example
illustrates::

    struct UpdateParentRev
        doc:
            On a write conflict, overwrite the existing file if the parent rev matches.

        parent_rev String:
            The revision to be updated.
        auto_rename Boolean:
            Whether the new file should be renamed on a conflict.

        example default
            parent_rev="abc123"
            auto_rename=false

    union WriteConflictPolicy
        doc:
            Policy for managing write conflicts.

        reject:
            On a write conflict, reject the new file.
        overwrite:
            On a write conflict, overwrite the existing file.
        rename:
            On a write conflict, rename the new file with a numerical suffix.
        update_if_matching_parent_rev UpdateParentRev:
            On a write conflict, overwrite the existing file.


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
       doc:
           An example.

       created DbxTimestamp:
           When this example was created.

Operations
----------

Operations map to your API endpoints. You specify a list of data types for the request,
and a list of data types for the response::

    struct AccountInfoRequest
        doc:
            Input to request.

        account_id String = "me":
            A user's account identifier. Use "me" to get information for the
            current account.

    op GetInfo
        doc:
            Get user account information.

        request
            AccountInfoRequest
        response
            AccountInfo

.. _default_value_example:

Note that ``account_id`` was given a default value of ``"me"``. This is useful
for including in generated SDKs.

The following is an example of an endpoint with two request segments::

    struct FileUploadRequest
        doc:
            Stub.

        path String:
            The full path to the file you want to write to. It should not point
            to a folder.
        write_conflict_policy WriteConflictPolicy:
            Action to take if a file already exists at the specified path.

        example default
            path="Documents/plan.docx"

    op Upload
        doc:
            Upload a file to dropbox.

        request
            FileUploadRequest
            Binary

        response
            FileInfo

Documentation
-------------

To help template writers tailor documentation to a language, we support stubs
in documentation. Stubs are of the following format::

    :tag:`value`

Supported tags are ``op``, ``struct``, ``field``, and ``link``.

op
    A reference to an operation. Template writers should make a reference to
    the method that represents the operation.
struct
    A reference to a struct. Template writers should make a reference to the
    class that represents the struct.
field
    A reference to a field of a struct. It's intended for referencing
    parameters for functions, but its utility is still TBD.
link
    A hyperlink. Template writers should convert this to the proper hyperlink
    format for the language.

Defining a Code Generator
=========================

A code generator is a Python class which will generate code for a target language
given an API description. A code generator must satisfy the following conditions:

1. The filename must have '.babelt.py' as its extension. For example,
   base_namespace.babelt.py

2. A class must exist in the file that extends the
   ``babelapi.generator.generator.CodeGenerator`` class and implements the
   abstract ``generate()`` method. BabelAPI automatically detects subclasses
   and calls the ``generate()`` method.

Using the API Object
--------------------

Code generators have a ``self.api`` member variable. The object is an instance
of the ``babelapi.api.Api`` class. From this object, you can access all the
defined namespaces, data types, and operations. See the Python object definition
for more information.

Example
-------

Here's an example of a minimal generator of Python code::

   from babelapi.generator.generator import CodeGeneratorMonolingual
   from babelapi.lang.python import PythonTargetLanguage

   # Optionally define a string that contains code that you want to appear
   # in auto generated files, but that doesn't need any tailoring to the spec.
   base = """\
   import os

   """

   # CodeGeneratorMonolingual is a simple child class of CodeGenerator that
   # enforces that self.lang is mapped to a TargetLanguage.
   class ExamplePythonGenerator(CodeGeneratorMonolingual):

       # PythonTargetLanguage has helper methods for formatting class, obj
       # and variable names (some languages use underscores to separate words,
       # others use camelcase.
       lang = PythonTargetLanguage()

       def generate(self):
           """Generates a module for each namespace."""
           for namespace in self.api.namespaces.values():
               # One module per namespace is created. The module takes the name
               # of the namespace.
               with self.output_to_relative_path('{}.py'.format(namespace.name)):
                   self._generate_namespace_module(namespace)

    def _generate_namespace_module(self, namespace):
        """Creates a module for the namespace. All data types are represented
        as classes. The operations are added to a class that takes the name of
        the namespace."""

        # Emit boilerplate you've defined.
        self.emit(base)

        # When we generate classes to represent the data types in the Spec,
        # we need to differentiate between structs and unions as they behave
        # differently.
        for data_type in namespace.linearize_data_types():
            if isinstance(data_type, Struct):
                self._generate_struct_class(data_type)
            elif isinstance(data_type, Union):
                self._generate_union_class(data_type)
            else:
                raise TypeError('Cannot handle type %r' % type(data_type))

        # Put all operations in a class that will have one method per class.
        self.emit_line('class {}(Namespace):'.format(self.lang.format_class(namespace.name)))
        with self.indent():
            for operation in namespace.operations:
                self._generate_operation(namespace, operation)


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
