******************
Language Reference
******************

To illustrate how to write a spec, we're going to dissect a spec that defines
a hypothetical route that shows up in some form or another in most APIs for
web services: querying the account information for a user.

The spec should live in a file called ``users.babel``::

    # We put this in the "users" namespace in anticipation that
    # there would be many user-account-related routes.
    namespace users

    # We define an AccountId as being a 10-character string
    # once here to avoid declaring it each time.
    alias AccountId = String(min_length=10, max_length=10)

    struct BasicAccount
        "Basic information about a user's account."

        account_id AccountId
            "A unique identifier for the user's account."
        email String(pattern="^[^@]+@[^@]+\.[^@]+$")
            "The e-mail address of the user."

    union Status
        active
            "The account is active."
        inactive Timestamp(format="%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

    struct Account extends BasicAccount
        "Information about a user's account."

        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status
            "The status of the account."

        example default "A regular user"
            account_id="id-48sa2f0"
            email="alex@example.org"
            name="Alexander the Great"

    # This struct represents the input data to the route.
    struct GetAccountReq
        account_id AccountId

    # This union represents the possible errors that might be returned.
    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied Any
            "Insufficient privileges to query account information."
        unknown*

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

.. filename:

Choosing a Filename
===================

All specifications should use the extension ``.babel``. We recommend that the
name of the file be the same as the namespace (explained below) defined in the
spec. If the definitions for a namespace are spread across multiple files, we
recommend that all spec files use the namespace as a filename prefix. For
example, ``users_public.babel`` and ``users_private.babel``.

.. comments:

Comments
========

Any line whose first non-whitespace character is a hash ``#`` is considered a
comment and ignored by the parser. Use comments to explain parts of the spec
to a reader of the spec. Comments are distinct from documentation strings,
which are parsed and accessible to generators.

.. namespace:

Namespace
=========

Specs must begin with a namespace declaration as is the case here::

   namespace users

This logically groups all of the routes and data types in the spec file into
the ``users`` namespace. A spec file may only be part of one namespace.

Namespaces are useful for grouping related functionality together. For example,
the Dropbox API has a namespace devoted to all file operations (uploading,
downloading, ...), and another namespace for all operations relevant to user
accounts.

.. primitive-types:

Primitive Types
===============

In the example, ``String`` and ``Timestamp`` are primitive types. Here's a
table of all primitive types and the arguments they take:

======================= =======================================================
Type                    Arguments (**bold** are required)
======================= =======================================================
Binary                  --
Boolean                 --
Float{32,64}            --
Int{32,64}, UInt{32,64} * min_value
                        * max_value
List                    * **data_type**: A primitive or composite type that the
                          homogeneous list contains.
                        * min_items
                        * max_item
String                  * min_length
                        * max_length
                        * pattern: A regular expression to be used for
                          validation.
Timestamp               * **format**: Used by the JSON-serializer since no
                          native timestamp type is supported.
======================= =======================================================

If no arguments are needed, the parentheses can be omitted. For example::

    struct Example
        number Int64
        string String

.. struct:

Struct
======

A struct is a user-defined type made up of fields that have their own types::

    struct BasicAccount
        "Basic information about a user's account.

        This can be multi-line."

        account_id AccountId
            "A unique identifier for the user's account."
        email String(pattern="^[^@]+@[^@]+\.[^@]+$")
            "The e-mail address of the user."

A struct can be documented by specifying a string immediately following the
struct declaration. The string can be multiple lines, as long as each
subsequent line is at least at the indentation of the starting quote.
Read more about documentation strings here.

After the documentation is a list of fields. Fields are formatted with the field
name first followed by the field type. To provide documentation for a field,
specify a string on a new indented line following the field declaration.

.. struct-inheritance:

Inheritance
-----------

Using the ``extends`` keyword, a struct will inherit all the fields of another
struct::

    struct Account extends BasicAccount

``Account`` inherits ``account_id`` and ``email`` from ``BasicAccount``.

.. struct-composition:

Composition
-----------

User-defined types can be composed of other user-defined types, either
structs or unions::

    union Status
        active
            "The account is active."
        inactive Timestamp(format="%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

    struct Account extends BasicAccount
        "Information about a user's account."

        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status
            "The status of the account."

.. struct-nullable:

Nullable Type
-------------

When a field type is followed by a ``?``, the field is nullable::

    name String(min_length=1)?

Nullable means that the field can be unspecified, ie. ``null``. Code generators
should use a language's native facilities for null,
`boxed types <http://en.wikipedia.org/wiki/Object_type_(object-oriented_programming)#Boxing>`_,
and `option types <http://en.wikipedia.org/wiki/Option_type>`_ if possible. For
languages that do not support these features, a separate function to check for
the presence of a field is the preferred method.

A nullable type is considered optional. If it is not specified in a message,
the receiver should not error, but instead treat the field as absent.

.. struct-defaults:

Defaults
--------

A field with a primitive type can have a default set with a ``=`` followed by
a value at the end of the field declaration::

    struct Example
        number UInt64 = 1024
        string String = "hello, world."

Setting a default means that a field is optional. If it is not specified in a
message, the receiver should not error, but instead return the default when
the field is queried. The receiver should, however, track the fact that the
field was unspecified, so that if the message is re-serialized the default is
not present in the message.

Note also that a default cannot be set for a nullable type. Nullable types
implicitly have a default of ``null``.

In practice, defaults are useful when `evolving a spec <evolve_spec.rst>`_.

.. struct-examples:

Illustrative Examples
---------------------

Examples help you include realistic samples of data in definitions. This gives
spec readers a concrete idea of the what typical values will look like. Also,
examples help demonstrate how distinct fields might interact with each other.
Lastly, generators have access to examples, which is useful when automatically
generating documentation.

An example is declared by using the ``example`` keyword followed by a label,
and optionally a descriptive string. By convention, "default" should
be used as the label name for an example that can be considered a good
representation of the general case for the type::

    struct Account extends BasicAccount
        "Information about a user's account."

        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status
            "The status of the account."

        example default "A regular user"
            account_id="id-48sa2f0"
            email="alex@example.org"
            name="Alexander the Great"

        example unnamed "An unnamed user"
            account_id="id-29sk2p1"
            email="anony@example.org"
            name=null

As you can see, ``null`` should be used to mark that a nullable field is not
present.

.. union:

Union
=====

A union in Babel is a tagged union. A union can only "be" one of its variants
at any given time. Like a struct, it starts with a name declaration followed
by a documentation string::

    union Status
        active
            "The account is active."
        inactive Timestamp(format="%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

Its list of fields are a list of variants.

.. union-symbol:

Symbol
------

``active`` is a tag that is not mapped to any value. We call these symbols.

.. union-catch-all:

Catch All Symbol
----------------

By default, we consider unions to be closed. That is, for the sake of backwards
compatibility, a recipient of a message should never encounter a variant that
it isn't aware of. A recipient can therefore confidently handle the case where
a user is ``active`` or ``inactive`` and trust that no other value will ever
be encountered.

Because we anticipate that this will be constricting for APIs undergoing
evolution, we've introduced the notion of a "catch all" symbol. If a recipient
receives a tag that it isn't aware of, it will default the union to the catch
all symbol variant.

The notation is simply an ``*`` that follows a symbol variant::

    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied Any
            "Insufficient privileges to query account information."
        unknown*

In the example above, a recipient should have written code to handle
``no_account``, ``perm_denied``, and ``unknown``. If a tag that was not
previously known is received (e.g. ``bad_account``), the union will default
to the ``unknown`` tag.

We expect this to be especially useful for unions that represent the possible
errors an endpoint might return. Recipients in the wild may have been generated
with only a subset of the current errors, but they'll continue to function as
long as they handle the catch all tag.

.. union-any:

Any Data Type
-------------

Changing a symbol field to some data type is a backwards incompatible change.
After all, if a recipient is expecting a symbol and gets back a struct, it
isn't likely the handling code will be prepared.

To avoid this, set the field to the ``Any`` type as was done here::

    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied Any
            "Insufficient privileges to query account information."
        unknown*

Now, without causing a backwards incompatibility, the data type can be
updated to include more information::

    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied String
            "Insufficient privileges to query account information. The value
            is text explaining why."
        unknown*

.. alias:

Alias
=====

Sometimes we prefer to use an alias, rather than re-declaring a type over an
over again::

    alias AccountId = String(min_length=10, max_length=10)

In our example, declaring an ``AccountId`` alias is clearer when used and
will make it easier to change in the future.

.. route:

Route
=====

Routes correspond to your API endpoints::

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

The route is named ``get_account``. ``GetAccountReq`` is the data type of
the request to the route. ``Account`` is the data type of a response from the
route. ``GetAccountErr`` is the data type of an error response.

Similar to structs and unions, a documentation string must follow the route
name declaration.

A full description of an API route tends to require vocabulary that is specific
to a service. For example, the Dropbox API needs a way to specify some routes
as including a binary body (uploads) for requests. Another example is specifying
which routes can be used without authentication credentials.

To cover this open ended use case, routes can have an ``attrs`` section declared
followed by an arbitrary set of ``key=value`` pairs::

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

        attrs
            key1="value1"
            key2=1234
            key3=3.14
            key4=false

Code generators will populate a route object with these attributes.

.. documentation:

Documentation
=============

Documentation strings are an important part of specifications, which is why
they're a part of routes, structs, struct fields, unions, and union variants.
It's expected that there should be documentation for almost every place that
documentation strings are possible. It's not required only because some
definitions are self-explanatory or adding documentation would be redundant, as
is often the case when a struct field (with a doc) references another struct
(with a doc).

Documentation is accessible to generators. Code generators will inject
documentation into the language objects that represent routes, structs, and
unions. Generators for API documentation will find documentation strings
especially useful.

.. documentation-stubs:

Stubs
-----

Stubs help tailor documentation strings to a specific language. Stubs are of
the following format::

    :tag:`value`

Supported tags are ``route``, ``struct``, ``field``, ``link``, and ``val``.

route
    A reference to a route. Code generators should reference the class that
    represents the route.
type
    A reference to a data type, whether a primitive or composite type.
field
    A reference to a field of a struct or a variant of a union.
link
    A hyperlink. The format of the value is "<description...> <url>".
    Generators should convert this to a hyperlink for the target language.
val
    A value. Generators should convert this to the native representation of the
    value for the target language.

.. include:

Include
=======

Including header files is covered in
`Managing Large Specs: Using Headers <managing_large_specs.rst#using-headers>`_.

.. formal-grammar:

Formal Grammar
===============

Specification::

    Spec ::= Namespace Include* Definition*
    Namespace ::= 'namespace' Identifier
    Include ::= 'include' Identifier
    Definition ::= Alias | Route | Struct | Union
    PrimitiveType ::= Binary | Boolean | Float32 | Float64 | Int32 | Int64
                  | UInt32 | UInt64 | String | Timestamp
    Alias ::= 'alias' Identifier '=' PrimitiveType
    Inheritance ::= 'extends' Identifier
    Struct ::= 'struct' Identifier Inheritance?
    Union ::= 'union' Identifier
    Route ::= 'route' Identifier '(' Identifier ',' Identifier ',' Identifier ')'

TODO: Finish this section.
