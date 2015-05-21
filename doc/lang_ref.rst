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
        inactive Timestamp("%a, %d %b %Y %H:%M:%S")
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
        perm_denied
            "Insufficient privileges to query account information."
        unknown*

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

Choosing a Filename
===================

All specifications must have a ``.babel`` extension. We recommend that the
name of the file be the same as the `namespace <#ns>`_ defined in the spec.

`Headers <#include>`_ must use the ``.babelh`` extension.

Comments
========

Any text between a hash ``#`` and a newline is considered a comment. Comments
can take up an entire line, or they can be added to the end of a line.

Use comments to explain a section of the spec to a reader of the spec. Unlike
`documentation <#documentation>`_ strings, comments are not accessible to
generators as they are ignored by the parser.

.. _ns:

Namespace
=========

Specs must begin with a namespace declaration as is the case here::

   namespace users

This logically groups all of the routes and data types in the spec file into
the ``users`` namespace. A spec file must declare exactly one namespace, but
multiple spec files may contribute to the same namespace.

Namespaces are useful for grouping related functionality together. For example,
the Dropbox API has a namespace devoted to all file operations (uploading,
downloading, ...), and another namespace for all operations relevant to user
accounts.

Primitive Types
===============

In the example, ``String`` and ``Timestamp`` are primitive types. Here's a
table of all primitive types and the arguments they take:

======================= ================================= =====================
Type                    Arguments (**bold** are required  Notes
                        and positional)
======================= ================================= =====================
Binary                  --                                An array of bytes.
Boolean                 --
Float{32,64}            * min_value
                        * max_value
Int{32,64}, UInt{32,64} * min_value
                        * max_value
List                    * **data_type**: A primitive or   Lists are homogeneous.
                          composite type.
                        * min_items
                        * max_items
String                  * min_length                      A unicode string.
                        * max_length
                        * pattern: A regular expression
                          to be used for validation.
Timestamp               * **format**: Specified as a      This is used by the
                          string understood by            JSON-serializer since
                          strptime().                     it has no native
                                                          timestamp data type.
Void                    --
======================= ================================= =====================

Positional arguments (bold in the above table) are always required and appear
at the beginning of an argument list::

    struct ShoppingList
        items List(String)

Keyword arguments are optional and are preceded by the argument name and an
``=``::

    struct Person
        age UInt64(max_value=130)

If no arguments are needed, the parentheses can be omitted::

    struct Example
        number Int64
        string String

Here are some more examples::

    struct Coordinate
        x Int64
        y Int64

    struct Example
        f1 Binary
        f2 Boolean
        f3 Float64(min_value=0)
        # List of primitive types
        f4 List(Int64)
        # List of user-defined types
        f5 List(Coordinate, max_items=10)
        f6 String(pattern="^[A-z]+$")
        f7 Timestamp("%a, %d %b %Y %H:%M:%S +0000")

Mapping to a Target Language
----------------------------

Code generators map the primitive types of Babel to types in a target language.
For more information, consult the appropriate guide in `Using Generated Code
<using_generator.rst>`_.

Alias
=====

Sometimes we prefer to use an alias, rather than re-declaring a type over and
over again::

    alias AccountId = String(min_length=10, max_length=10)

In our example, declaring an ``AccountId`` alias makes future references to it
clearer since the name provides an extra semantic hint::

    struct BasicAccount
        "Basic information about a user's account."

        account_id AccountId
            "A unique identifier for the user's account."

    struct GetAccountReq
        account_id AccountId

Aliases also make refactoring easier. We only need to change the definition of
the ``AccountId`` alias to change it everywhere.

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
Refer to `Documentation`_ for more.

After the documentation is a list of fields. Fields are formatted with the field
name first followed by the field type. To provide documentation for a field,
specify a string on a new indented line following the field declaration.

Inheritance
-----------

Using the ``extends`` keyword, a struct can declare itself a subtype of another
struct, known as the supertype. The subtype inherit all the fields of the
supertype::

    struct Account extends BasicAccount

``Account`` inherits ``account_id`` and ``email`` from ``BasicAccount``.

A feature common to object-oriented programming, a subtype may be used in place
of a supertype.

Composition
-----------

User-defined types can be composed of other user-defined types, either
structs or unions::

    union Status
        active
            "The account is active."
        inactive Timestamp("%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

    struct Account extends BasicAccount
        "Information about a user's account."

        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status
            "The status of the account."

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

A default cannot be set for a nullable type. Nullable types implicitly have a
default of ``null``.

A default can be set for a field with a union data type, but only to a union
member with a void type. Using the example of ``Account``, the ``status`` can
be set to ``active`` by default::

    struct Account extends BasicAccount
        "Information about a user's account."

        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status = active
            "The status of the account."

In practice, defaults are useful when `evolving a spec <evolve_spec.rst>`_.

Examples
--------

Examples let you include realistic samples of data in definitions. This gives
spec readers a concrete idea of what typical values will look like. Also,
examples help demonstrate how distinct fields might interact with each other.

Generators have access to examples, which is useful when automatically
generating documentation.

An example is declared by using the ``example`` keyword followed by a label
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
            account_id = "id-48sa2f0"
            email = "alex@example.org"
            name = "Alexander the Great"

        example unnamed "An anonymous user"
            account_id = "id-29sk2p1"
            email = "anony@example.org"
            name = null

Every required field (not nullable and no default) must be specified, otherwise
an error will be returned. ``null`` can be used to mark that a nullable type
is not present.

When you have a set of nested types, each type defines examples for primitive
fields only. Here's an example where ``Name`` is now its own struct::

    struct Account extends BasicAccount

        name Name

        example default
            account_id = "id-48sa2f0"
            email = "alex@example.org"
            name = default

        example anonymous
            account_id = "id-29sk2p1"
            email = "anony@example.org"
            name = anonymous

    struct Name
        first_name String?

        example default
            first_name = "Alexander the Great"

        example anonymous
            first_name = null

As you can see, the ``anonymous`` example for ``Account`` explicitly references
the ``anonymous`` example for ``Name``.

Examples for unions must only specify one field, since only one union member
can be selected at a time. For example::

    union Owner
        nobody
        account Account
        organization String

        example default
            nobody = null

        example person
            account = default

        example group
            organization = "Dropbox"

In the ``default`` example, notice that void tags are specified with a value of
``null``. In the ``person`` example, the ``default`` example for the
``Account`` type is referenced.

Union
=====

A union in Babel is a
`tagged union <http://en.wikipedia.org/wiki/Tagged_union>`_. Think of it as a
type that can store one of several different possibilities at a time. Each
possibility has an identifier that is called a "tag". In our example, the union
``Status`` has tags ``active`` and ``inactive``::

    union Status
        "The status of a user's account."

        active
            "The account is active."
        inactive Timestamp("%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

A tag is associated with a type (``inactive`` stores a ``Timestamp``). If the
type is omitted as in the case of ``active``, the type is implicitly ``Void``.

The primary advantage of a union is its logical expressiveness. You'll often
encounter types that are best described as choosing between a set of options.
Avoid the common anti-pattern of using a struct with a nullable field for each
option, and relying on your application logic to enforce that only one is set.

Another advantage is that for languages that support tagged unions, the
compiler can check that your application code handles all possible cases and
that accesses are safe. Generators will take advantage of such features when
they are available in the target language.

Like a struct, a documentation string can follow the union declaration and/or
follow each tag definition.

Catch-all Tag
-------------

By default, we consider unions to be closed. That is, for the sake of backwards
compatibility, a recipient of a message should never encounter a tag that it
isn't aware of. A recipient can therefore confidently handle the case where a
user is ``active`` or ``inactive`` and trust that no other value will ever be
encountered.

Because we anticipate that this will be constricting for APIs undergoing
evolution, we've introduced the notion of a catch-all tag. If a recipient
receives a tag that it isn't aware of, it will default the union to the
catch-all tag.

The notation is simply an ``*`` that follows a tag with an omitted type, ie.
its type is Void::

    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied
            "Insufficient privileges to query account information."
        unknown*

In the example above, a recipient should have written code to handle
``no_account``, ``perm_denied``, and ``unknown``. If a tag that was not
previously known is received (e.g. ``bad_account``), the union will default
to the ``unknown`` tag.

We expect this to be especially useful for unions that represent the possible
errors a route might return. Recipients in the wild may have been generated
with only a subset of the current errors, but they'll continue to function
appropriately as long as they handle the catch-all tag.

Inheritance
-----------

Using the ``extends`` keyword, a union can declare itself as a supertype of
another union, known as the subtype. The supertype will have all the tags of
the subtype::

    union DeleteAccountError extends GetAccountError

``DeleteAccount`` inherits the tags ``no_account``, ``perm_denied``, and
``unknown`` from ``GetAccountError``. Since ``GetAccountError`` has already
defined a catch-all tag, ``DeleteAccountError`` or any other supertype cannot
declare another catch-all.

Note that the supertype/subtype relationship created by ``extends`` between two
unions is the opposite of an ``extends`` between two structs. It's stated this
way to maintain the invariant that a subtype may be used in place of a
supertype. Specifically, a ``GetAccountError`` can be used in place of
``DeleteAccountError`` because a handler will be prepared for all possibilities
of ``GetAccountError`` since they are a subset of ``DeleteAccountError``.


Struct With Enumerated Subtypes
===============================

If a struct enumerates its subtypes, an instance of any subtype will satisfy
the type constraint. This is useful when wanting to discriminate amongst types
that are part of the same hierarchy while simultaneously being able to avoid
discriminating when accessing common fields.

To declare the enumeration, define a union following the documentation string
of the struct if one exists. Unlike a regular union, it is unnamed. Each member
of the union specifies a tag followed by the name of a subtype. The tag (known
as the "type tag") is present in the serialized format to distinguish between
subtypes. For example::

    struct Resource
        "Sample doc."

        union
            file File
            folder Folder

        path String

    struct File extends Resource:
        ...

    struct Folder extends Resource:
        ...

Anywhere ``Resource`` is referenced, an instance of ``File`` or ``Folder``
satisfies the type constraint.

As you can infer, all leaf structs in the hierarchy will have no subtypes to
enumerate, and thus will omit the ``union`` section. If a leaf struct is
referenced as a type, it is indistinguishable from an ordinary struct
definition.

Enumerated subtypes have several additional constraints:

    * If a struct enumerates subtypes, its parent must also enumerate its own
      subtypes.
    * If a struct's parent enumerates subtypes, it must enumerate its own
      subtypes if it has any.
    * Type tags cannot match the names of any of the struct fields.

Catch-all
---------

Similar to a union, a struct with enumerated types can be labeled as a
catch-all. This is done by appending an asterix, ``*``, to the ``union``::

    struct Resource
        "Sample doc."

        union*
            file File
            folder Folder

        path String

    struct File extends Resource:
        ...

    struct Folder extends Resource:
        ...

If recipient receives a tag for a subtype that it is unaware of, it will
substitute the base struct in its place if it's a catch-all. In the example
above, if the subtype is a ``Symlink`` (not shown), then the recipient will
return a ``Resource`` in its place.

Nullable Type
=============

When a type is followed by a ``?``, the type is nullable::

    name String(min_length=1)?

Nullable means that the type can be unspecified, ie. ``null``. Code generators
should use a language's native facilities for null,
`boxed types <http://en.wikipedia.org/wiki/Object_type_(object-oriented_programming)#Boxing>`_,
and `option types <http://en.wikipedia.org/wiki/Option_type>`_ if possible. For
languages that do not support these features, a separate function to check for
the presence of a type is the preferred method.

A nullable type is considered optional. If it is not specified in a message,
the receiver should not error, but instead treat it as absent.

Route
=====

Routes correspond to your API endpoints::

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

The route is named ``get_account``. ``GetAccountReq`` is the data type of
the request to the route. ``Account`` is the data type of a response from the
route. ``GetAccountErr`` is the data type of an error response.

Similar to structs and unions, a documentation string may follow the route
signature.

Attributes
----------

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

Import
======

You can refer to types and aliases in other namespaces by using the ``import``
directive.

For example, we can move the definition of ``AccountId`` and ``BasicAccount``
into a file called ``common.babel``::

    namespace common

    # We define an AccountId as being a 10-character string
    # once here to avoid declaring it each time.
    alias AccountId = String(min_length=10, max_length=10)

    struct BasicAccount
        "Basic information about a user's account."

        account_id AccountId
            "A unique identifier for the user's account."
        email String(pattern="^[^@]+@[^@]+\.[^@]+$")
            "The e-mail address of the user."

Now in ``users.babel``, we add an ``import`` statement under the namespace
directive as follows::

    namespace users

    import common

When referencing data types in ``common``, use the prefix ``common.``. For
example, ``common.AccountId`` and ``common.BasicAccount``.

.. _doc:

Documentation
=============

Documentation strings are an important part of specifications, which is why
they can be attached to routes, structs, struct fields, unions, and union
options. It's expected that most elements should be documented. It's not
required only because some definitions are self-explanatory or adding
documentation would be redundant, as is often the case when a struct field
(with a doc) references a struct (with a doc).

Documentation is accessible to generators. Code generators will inject
documentation into the language objects that represent routes, structs, and
unions. Generators for API documentation will find documentation strings
especially useful.

.. _doc-refs:

References
----------

References help generators tailor documentation strings for a target
programming language.

References have the following format::

    :tag:`value`

Supported tags are ``route``, ``type``, ``field``, ``link``, and ``val``.

route
    A reference to a route. The value should be the name of the route. Code
    generators should reference the class or function that represents the route.
type
    A reference to a user-defined data type (Struct or Union). The value should
    be the name of the user-defined type.
field
    A reference to a field of a struct or a tag of a union. If the field being
    referenced is a member of a different type than the docstring, then use the
    format `TypeName.field_name`. Otherwise, use just the field name as the
    value.
link
    A hyperlink. The format of the value is ``<title...> <uri>``, e.g.
    ``Babel Repo https://github.com/dropbox/babelapi``. Everything after the
    last space is considered the URI. The rest is treated as the title. For
    this reason, you should ensure that your URIs are
    `percent encoded <http://en.wikipedia.org/wiki/Percent-encoding>`_.
    Generators should convert this to a hyperlink understood by the target
    language.
val
    A value. Supported values include ``null``, ``true``, ``false``, integers,
    floats, and strings. Generators should convert the value to the native
    representation of the value for the target language.

Formal Grammar
===============

Specification::

    Spec ::= Namespace Import* Definition*
    Namespace ::= 'namespace' Identifier
    Import ::= 'import' Identifier
    Definition ::= Alias | Route | Struct | Union
    Alias ::= 'alias' Identifier '=' TypeRef

Struct::

    Struct ::= 'struct' Identifier Inheritance? NL INDENT Doc? Subtypes? Field* Example* DEDENT
    Inheritance ::= 'extends' Identifier
    SubtypeField ::= Identifier TypeRef NL
    Subtypes ::= 'union' NL INDENT SubtypeField+ DEDENT
    Default ::= '=' Literal
    Field ::= Identifier TypeRef Default? (NL INDENT Doc DEDENT)?

Union::

    Union ::= 'union' Identifier NL INDENT (VoidTag|Tag)* DEDENT
    VoidTag ::= Identifier '*'? (NL INDENT Doc DEDENT)?
    Tag ::= Identifier TypeRef (NL INDENT Doc DEDENT)?

Route::

    Route ::= 'route' Identifier '(' TypeRef ',' TypeRef ',' TypeRef ')' (NL INDENT Doc DEDENT)?

Type Reference::

    Attributes ::= '(' (Identifier '=' (Literal | Identifier) ','?)*  ')'
    TypeRef ::= Identifier Attributes? '?'?

Primitives::

    PrimitiveType ::= 'Binary' | 'Boolean' | 'Float32' | 'Float64' | 'Int32'
                  | 'Int64' | 'UInt32' | 'UInt64' | 'String' | 'Timestamp'

Basic::

    Identifier ::= (Letter | '_')? (Letter | Digit | '_')* # Should we allow trailing underscores?
    Letter ::=  ['A'-'z']
    Digit ::=  ['0'-'9']
    Literal :: = BoolLiteral | FloatLiteral | IntLiteral | StringLiteral
    BoolLiteral ::= 'true' | 'false'
    FloatLiteral ::=  '-'? Digit* ('.' Digit+)? ('E' IntLiteral)?
    IntLiteral ::=  '-'? Digit+
    StringLiteral ::= '"' .* '"' # Not accurate
    Doc ::= StringLiteral # Not accurate
    NL = Newline
    INDENT = Incremental indentation
    DEDENT = Decremented indentation

Specification Header::

    SpecHeader ::= Definition*

TODO: Need to add additional information about handling of NL, INDENT, DEDENT,
and whitespace between tokens. Also, the attrs section of Routes and the
examples section of Structs haven't been addressed.
