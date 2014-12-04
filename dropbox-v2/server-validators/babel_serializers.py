"""
Serializers should marshal Babel data types into specific formats.

Currently, only JSON is supported. If possible, serializers should be kept
separate from the RPC format.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

import base64
import datetime
import json

from babel_data_types import (
    Binary,
    List,
    PrimitiveType,
    Struct,
    Timestamp,
    Union,
)

class JsonEncoder(object):
    """
    Example of serializing a struct to JSON:

    struct FileRef
       path String
       rev String

    >>> fr = FileRef()
    >>> fr.path = 'a/b/c'
    >>> fr.rev = '1234'
    >>> JsonEncoder.encode(fr)
    "{'path': 'a/b/c', 'rev': '1234'}"

    Example of serializing a union to JSON:

    union UploadMode
        add
        overwrite
        update FileRef

    >>> um = UploadMode()
    >>> um.set_add()
    >>> JsonEncoder.encode(um)
    '"add"'
    >>> um.update = fr
    >>> JsonEncoder.encode(um)
    "{'update': {'path': 'a/b/c', 'rev': '1234'}}"
    """

    @classmethod
    def encode(cls, obj, data_type=None):
        """Encodes a Babel data type into JSON."""
        return json.dumps(cls._encode_helper(obj, data_type))

    @classmethod
    def _encode_helper(cls, obj, data_type=None):
        """Encodes a Babel data type into a JSON-compatible dict."""

        # We can derive the data type of a struct or union since it's included
        # as class variables. But, the data type of primitive types is absent
        # and must be explicitly specified.
        assert data_type or isinstance(obj, (Struct, Union)), (
            'No data_type is provided -> obj must be a Struct or Union'
        )
        if isinstance(obj, Struct):
            d = {}
            for name, optional, field_data_type  in obj._fields_:
                val = getattr(obj, name)
                if val is not None:
                    d[name] = cls._encode_helper(val, field_data_type)
                elif val is None and not optional:
                    raise KeyError('missing required field {!r}'.format(name))
            return d
        elif isinstance(obj, Union):
            field_data_type = obj._fields_[obj._tag]
            if field_data_type:
                val = getattr(obj, obj._tag)
                if isinstance(field_data_type, PrimitiveType):
                    return cls._make_json_friendly(field_data_type, val)
                else:
                    return {obj._tag: cls._encode_helper(val)}
            else:
                return obj._tag
        elif isinstance(data_type, List):
            if not isinstance(obj, list):
                # TODO: Specify the field name in the error message
                raise ValueError(
                    'field is of type %r rather than a list'
                    % (type(obj).__name__)
                )
            return [cls._encode_helper(item, data_type.data_type) for item in obj]
        elif isinstance(data_type, PrimitiveType):
            return cls._make_json_friendly(data_type, obj)
        else:
            raise AssertionError('Unsupported data type %r'
                                 % type(data_type).__name__)

    @classmethod
    def _make_json_friendly(cls, data_type, val):
        """Convert a primitive type to a Python type that can be serialized
        by the json package."""
        if val is None:
            return val
        elif isinstance(data_type, Timestamp):
            return val.strftime(data_type.format)
        elif isinstance(data_type, Binary):
            return base64.b64encode(val)
        else:
            return val

class JsonDecoder(object):
    """Performs the reverse operation of JsonEncoder."""

    @classmethod
    def decode(cls, data_type, serialized_obj):
        return cls._decode_helper(data_type, json.loads(serialized_obj))

    @classmethod
    def _decode_helper(cls, data_type, obj):
        """
        Decodes a JSON-compatible object into an instance of a Babel data type.
        """
        if issubclass(data_type, Struct):
            for key in obj:
                if key not in data_type._field_names_:
                    raise KeyError('unknown field {!r}'.format(key))
            o = data_type()
            for name, optional, field_data_type in data_type._fields_:
                if name in obj:
                    setattr(o, name, cls._decode_helper(field_data_type, obj[name]))
                elif not optional:
                    raise KeyError('missing required field {!r}'.format(name))
        elif issubclass(data_type, Union):
            o = data_type()
            if isinstance(obj, str):
                # The variant is a symbol
                tag = obj
                if tag not in data_type._fields_:
                    raise KeyError('Unknown tag %r' % tag)
                getattr(o, 'set_' + tag)()
            elif isinstance(obj, dict):
                assert len(obj) == 1, 'obj must only have 1 key specified'
                tag, val = obj.items()[0]
                if tag not in data_type._fields_:
                    raise KeyError('Unknown option %r' % tag)
                setattr(o, tag, cls._decode_helper(data_type._fields_[tag], val))
            else:
                raise AssertionError('obj type %r != str or dict'
                                     % type(obj).__name__)
        elif isinstance(data_type, List):
            if not isinstance(obj, list):
                raise ValueError(
                    'field is of type %r rather than a list'
                    % (type(obj).__name__)
                )
            return [cls._decode_helper(data_type.data_type, item) for item in obj]
        elif isinstance(data_type, PrimitiveType):
            return cls._make_babel_friendly(data_type, obj)
        else:
            raise AssertionError('obj type %r != Struct or Union'
                                 % type(obj).__name__)
        return o

    @classmethod
    def _make_babel_friendly(cls, data_type, val):
        """Convert a Python object to a type that is accepted by a Babel
        data type."""
        if val is None:
            return val
        elif isinstance(data_type, Timestamp):
            return datetime.datetime.strptime(val, data_type.format)
        elif isinstance(data_type, Binary):
            return base64.b64decode(val)
        else:
            return val
