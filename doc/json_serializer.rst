***************
JSON Serializer
***************

Code generators include a JSON serializer which will convert a target
language's representation of Babel data types into JSON. This document explores
how Babel data types, regardless of language, are mapped to JSON.

Primitive Types
===============

========================== ====================================================
Babel Primitive            JSON Representation
========================== ====================================================
Binary                     String: Base64-encoded
Boolean                    Boolean
Float{32,64}               Number
Int{32,64}, UInt{32,64}    Number
List                       Array
String                     String
Timestamp                  String: Encoded using strftime() based on the
                           Timestamp's format argument.
Void                       Null
========================== ====================================================

Struct
======

A struct is represented as a JSON object. Each specified field has a key in the
object. For example::

    struct Coordinate
        x Int64
        y Int64


converts to::

    {
     "x": 1,
     "y": 2
    }

If an optional (has a default or is nullable) field is not specified, the key
should be omitted. For example, given the following spec::

    struct SurveyAnswer
        age Int64
        name String = "John Doe"
        address String?

If ``name`` and ``address`` are unset and ``age`` is 28, then the struct
serializes to::

    {
     "age": 28
    }

Setting ``name`` or ``address`` to ``null`` is not a valid serialization;
deserializers will raise an error.

Enumerated Subtypes
-------------------

A struct that enumerates subtypes serializes differently from a regular
struct. Here's an example to demonstrate::

    struct A
        union
            b B
            c C
        w Int64

    struct B extends A
        x Int64

    struct C extends A
        union*
            c1 C1
            c2 C2
        y Int64

    struct C1 extends C
        z Int64

    struct C2 extends C
        "No new fields."

Serializing ``A`` when it contains a struct ``B`` (with values of ``1`` for
each field) appears as::

    {
     "w": 1,
     "b": {
      "x": 1
     }
    }

Serializing ``A`` when it contains a struct ``C1`` appears as::

    {
     "w": 1,
     "c": {
      "y": 1,
      "c1": {
       "z": 1
      }
     }
    }

Serializing ``A`` when it contains a struct ``C2`` appears as::

    {
     "w": 1,
     "c": {
      "y": 1,
      "c2": {}
     }
    }

Note how type tags are treated identically to fields in the JSON object. A type
tag always has a JSON object as its value which contains data specific to the
referenced subtype.

If the recipient receives a tag it is unaware of, it should at first apply the
same policy it uses for fields it is unaware of. In fact, a recipient will be
unable to determine whether the unknown JSON object key refers to a type tag or
a field. The recipient should then determine if the tag refers to a struct
that's a catch-all. If so, it should return that base type, otherwise, the
message should be rejected.

For example::

    {
     "w": 1,
     "c": {
      "y": 1,
      "c3": {}
     }
    }

Because ``c3`` is unknown, the recipient checks that struct ``C`` is a
catch-all. Since it is, it deserializes the message to a ``C`` object.

Union
=====

A tag with an associated type is represented as a JSON object. The key is the
tag name, and the value is the tag value. For example::

    union U
        number Int64
        string String

If the ``number`` tag is populated with ``42``, this serializes to::

    {
      "number": 42
    }

In the case of a tag with a Void type, the union serializes to a string of the
tag name. For example::

    union U
        a
        b

This serializes to either::

    "a"

or::

    "b"

Likewise, if a tag has a nullable value that is unset, then the union
serializes to a string of the tag name. For example::

    union U
        a Int64?
        b String

If ``a`` is selected with an unset value, this serializes to::

    "number"

It is not a valid serialization to use a JSON object with a ``number`` key
and ``null`` value; deserializers will raise an error.
