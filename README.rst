****************
BabelSDK
****************

Define an API once in Babel. Use templates to define how the Babel definition
maps to any programming language. Compile from Babel to all target languages.

Babel makes no assumptions about the protocol layer being used to make API
requests and return responses; its first use case is the Dropbox v1 API which
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

Download or clone BabelSDK, and run the following in its root directory::

   $ sudo python setup.py install

This will install a script ``babelsdk`` to your PATH that can be run from the
command line::

   $ babelsdk -h

If you did not run ``setup.py`` but have the Python package in your PYTHONPATH,
you can replace ``babelsdk`` with ``python -m babelsdk.cli`` as follows::

   $ python -m babelsdk.cli -h

Simple Example
--------------

You can compile an example babel and apply it to a documentation template::

   $ babelsdk example/api/v2_files.babel example/api/v2_users.babel example/template/docs

You can view the generated documentation using::

   $ google-chrome example/template/docs/docs.html

Fundamentals
============

There are three types of files.

Babel (.babel extension)
------------------------

Babels define the data types and operations available in an API.

Babel Header (.babelh extension)
--------------------------------

Babel Headers define only data types available in an API. Headers can be
included in Babel files so that common data types can be re-used.

Babel Template (.babelt extension)
----------------------------------

BabelSDK will render a Babel Template based on an API defined in Babel. These
templates can be written in any templating language (currently only jinja2 is
supported).

Defining a Babel
================

A Babel is composed of a namespace followed by zero or more includes and zero or more definitions::

   Babel ::= Namespace Include* Definition*

Namespace
---------

Babels must begin with a namespace declaration::

   Namespace ::= 'namespace' Identifier

Example::

   namespace users

This is the namespace for all the operations and data types in the Babel. It
helps us separate different parts of the API like "files", "users", and
"photos".

Include
-------

Use an include to make all definitions in a Babel Header available::

   Include ::= 'include' Identifier

Example::

   include common

This will search for a file called ``common.babelh`` in the same directory
as the Babel.

Definition
----------

There are four types of definitions available::

   Definition ::= Alias | Struct | Union | Operation

Struct
------

A struct is a type made up of other types::

   struct QuotaInfo:
       doc::
           The space quota info for a user.

       quota UInt64::
           The user's total quota allocation (bytes).
       normal UInt64::
           The user's used quota outside of shared folders (bytes).
       shared UInt64::
           The user's used quota in shared folders (bytes).

       example default:
           quota=1000000
           normal=1000
           shared=500

A struct can optionally define a documentation string by declaring "doc::".
The double colon enters documentation mode and indicates that the following
text is free form. Documentation mode is terminated only by a line that is on
the same indent as the original "doc::" string.

After the documentation is a list of fields. Fields are formatted with the field name
first followed by the field type. To provide documentation for a field, use "::", otherwise
end the line with the field type.

Finally, examples can be declared. An example is declared by using the "example" keyword followed
by a label for the example. By convention, "default" should be used as the label name for an
example that can be considered a good representation of the general case for the type.

Types can also be composed of other types::

   struct Team:
       doc::
           Information relevant to a team.

       name String::
           The name of the team.

       example default:
           name="Acme, Inc."

   struct AccountInfo:
       doc::
           Information for a user's account.

       display_name String::
           The full name of a user.
       quota QuotaInfo::
           The user's quota.
       is_paired Boolean::
           Whether the user has a personal and business account.
       team Team|null::
           If this paired account is a member of a team.

       example default:
           display_name="Jon Snow"
           is_paired=true

       example unpaired:
           display_name="Jon Snow"
           is_paired=false
           team=null


Note in the example above that the ``AccountInfo.team`` field  was marked as nullable. By default,
fields do not accept ``null`` as a valid value.

A struct can also inherit from another struct using the "extends" keyword::

    struct EntryInfo:
        doc::
            A file or folder entry.

        id String(max_length=40)::
            A unique identifier for the file.
        id_rev UInt64::
            A unique identifier for the current revision of a file. This field is
            the same rev as elsewhere in the API and can be used to detect changes
            and avoid conflicts.
        path String::
            Path to file or folder.
        modified DbxDate|null::
            The last time the file was modified on Dropbox, in the standard date
            format (null for root folder).
        is_deleted Boolean::
            Whether the given entry is deleted.

    struct FileInfo extends EntryInfo:
        doc::
            Describes a file.

        size UInt64::
            File size in bytes.
        mime_type String|null::
            The Internet media type determined by the file extension.
        media_info MediaInfo optional::
            Information specific to photo and video media.

        example default:
            id="xyz123"
            id_rev=2
            path="/Photos/flower.jpg"
            size=1234
            mime_type="image/jpg"
            modified="Sat, 28 Jun 2014 18:23:21"
            is_deleted=false

Note the use of the ``optional`` keyword which denotes that the field may not
be present. How this is handled is language and implementation specific.

Union
-----

A union in Babel is a tagged union. In its field declarations, a tag name is followed by
a data type::

   struct PhotoInfo:
       doc::
           Photo-specific information derived from EXIF data.

       time_taken DbxDate::
           When the photo was taken.
       lat_long List(data_type=Float)|null::
           The GPS coordinates where the photo was taken.

       example default:
           time_taken="Sat, 28 Jun 2014 18:23:21"
           lat_long=null

   struct VideoInfo:
       doc::
           Video-specific information derived from EXIF data.

       time_taken DbxDate::
           When the photo was taken.
       lat_long List(data_type=Float)|null::
           The GPS coordinates where the photo was taken.
       duration Float::
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

    struct UpdateParentRev:
        doc::
            On a write conflict, overwrite the existing file if the parent rev matches.

        parent_rev String::
            The revision to be updated.
        auto_rename Boolean::
            Whether the new file should be renamed on a conflict.

        example default:
            parent_rev="abc123"
            auto_rename=false

    union WriteConflictPolicy:
        doc::
            Policy for managing write conflicts.

        reject::
            On a write conflict, reject the new file.
        overwrite::
            On a write conflict, overwrite the existing file.
        rename::
            On a write conflict, rename the new file with a numerical suffix.
        update_if_matching_parent_rev UpdateParentRev::
            On a write conflict, overwrite the existing file.


Primitives
----------

These types exist without having to be declared:

   * Boolean
   * Integers: Int32, Int64, UInt32, UInt64
      * Attributes ``min_value`` and ``max_value`` can be set for more
        restrictive bounding.
   * Float, Double
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

   struct Example:
       doc::
           An example.

       created DbxTimestamp

Operations
----------

Operations map to your API endpoints. You specify a list of data types for the request,
and a list of data types for the response::

    struct AccountInfoRequest:
        doc::
            Input to request.

        account_id String = "me"::
            A user's account identifier. Use "me" to get information for the
            current account.

    op Info:
        doc::
            Get user account information.

        request:
            in AccountInfoRequest

        response:
            info AccountInfo

Note that ``account_id`` was given a default value of ``"me"``. This is useful
for including in generated SDKs.

Each "segment" of a request or response has a name ("in" and "info" above). It
is recommended that this name be used as the name of the accessor in generated
SDKs.

The following is an example of an endpoint with two request segments::

    struct FileUploadRequest:
        doc::
            Stub.

        path String::
            The full path to the file you want to write to. It should not point
            to a folder.
        write_conflict_policy WriteConflictPolicy::
            Action to take if a file already exists at the specified path.

        example default:
            path="Documents/plan.docx"

    op Upload:
        doc::
            Upload a file to dropbox.

        request:
            in FileUploadRequest
            file Binary

        response:
            info FileInfo

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

Defining a Babel Template
=========================

A Babel template is a file used to auto generate code for a target language. A
template must satisfy the following conditions:

1. The filename must have '.babelt' as its inner extension. For example,
   files.babelt.py

   * This makes it easy to search for a file (especially in an IDE), since
     the prefix is still "files".
   * IDEs that use the outer extension to determine syntax highlighting
     will continue to work.

2. The first line of the file must include ``babelsdk(jinja2)``.

   * You'll want to make the first line a comment in the target language.

      * ``# babelsdk(jinja2)`` for Python
      * ``<!-- babelsdk(jinja2) -->`` for HTML

   * jinja2 is currently the only available generator. But, this allows for
     a pluggable architecture for templating engines.

Jinja2 Templating
-----------------

You'll want to familiarize yourself with templating in
`jinja2 <http://jinja.pocoo.org/docs/>`_. Your template will have access to the
``api`` variable, which maps to the ``babelsdk.api.Api`` object. From this
object, you can access all the defined namespaces, data types, and operations.
See the Python object definition for more information.

You also have access to filters to help tailor the API Definition to the target
language. For example, you can use ``{{ variable }}|class`` to convert the
variable to the standard format for a class (capitalized words). The full list
of available filters is:

class
    Converts a name to the format of a class name.
method
    Converts a name to the format of a method name.
type
    Converts a primitive data type to the name of primitive type.
pprint
    Outputs a primitive as a literal.

These filters are tailored per language.

Target SDKs
===========

* Python
* Ruby
* Java
* PHP
* Objective-C

Other Targets
=============

* Web Docs
* Server Input Validation
* Server Output Validation

General Rules
=============

* Clients must accept new fields (ie. fields unknown to it), and ignore them.
* Server should be flexible on missing inputs (backwards compatibility), but strict on what goes out.
