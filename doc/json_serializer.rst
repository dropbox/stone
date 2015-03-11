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

In the case of a symbol, the union serializes to a string of the tag name.
For example::

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

The Any data type serializes as a symbol. However, a deserializer must not
assume that an Any will be received as a symbol. It must handle the symbol
case, and the case where the Any has been converted to another data type.
