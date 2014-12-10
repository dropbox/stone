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
import six

from babel_data_types import (
    Binary,
    List,
    PrimitiveType,
    Struct,
    Timestamp,
    Union,
    ValidationError,
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
        if isinstance(data_type, List):
            if not isinstance(obj, list):
                # TODO: This could be better...
                raise ValidationError(
                    'Expected list, got %s'
                    % (type(obj).__name__)
                )
            return [cls._encode_helper(item, data_type.data_type) for item in obj]
        elif isinstance(data_type, PrimitiveType):
            return cls._make_json_friendly(data_type, obj)
        elif isinstance(data_type, Struct):
            d = {}
            for name, optional, field_data_type  in data_type.data_type._fields_:
                val = getattr(obj, name)
                if val is not None:
                    d[name] = cls._encode_helper(val, field_data_type)
                elif val is None and not optional:
                    raise KeyError('missing required field {!r}'.format(name))
            return d
        elif isinstance(data_type, Union):
            field_data_type = data_type.data_type._fields_[obj._tag]
            if field_data_type:
                val = getattr(obj, obj._tag)
                if isinstance(field_data_type, PrimitiveType):
                    return cls._make_json_friendly(field_data_type, val)
                else:
                    return {obj._tag: cls._encode_helper(val)}
            else:
                return obj._tag
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
    def decode(cls, data_type, serialized_obj, strict=True):
        """If strict, then unknown keys in serialized_obj will raise an error."""
        return cls._decode_helper(data_type, json.loads(serialized_obj), strict)

    @classmethod
    def _decode_helper(cls, data_type, obj, strict):
        """
        Decodes a JSON-compatible object based on its Babel data type into a
        representative Python object.
        """
        if isinstance(data_type, Struct):
            if strict:
                for key in obj:
                    if key not in data_type.data_type._field_names_:
                        raise ValidationError('unknown field {!s}'.format(key))
            o = data_type.data_type()
            for name, optional, field_data_type in data_type.data_type._fields_:
                if name in obj:
                    v = cls._decode_helper(field_data_type, obj[name], strict)
                    setattr(o, name, v)
            data_type.validate(o)
        elif isinstance(data_type, Union):
            o = data_type.data_type()
            if isinstance(obj, six.string_types):
                # The variant is a symbol
                tag = obj
                if tag not in data_type.data_type._fields_:
                    raise ValidationError('Unknown tag %r' % tag)
                getattr(o, 'set_' + tag)()
            elif isinstance(obj, dict):
                assert len(obj) == 1, 'obj must only have 1 key specified'
                tag, val = obj.items()[0]
                if tag not in data_type.data_type._fields_:
                    raise ValidationError('Unknown option %r' % tag)
                v = cls._decode_helper(data_type.data_type._fields_[tag], val, strict)
                setattr(o, tag, v)
            else:
                raise AssertionError('obj type %r != str or dict'
                                     % type(obj).__name__)
        elif isinstance(data_type, List):
            if not isinstance(obj, list):
                raise ValidationError(
                    'field is of type %r rather than a list'
                    % (type(obj).__name__)
                )
            return [cls._decode_helper(data_type.data_type, item, strict)
                    for item in obj]
        elif isinstance(data_type, PrimitiveType):
            return cls._make_babel_friendly(data_type, obj)
        else:
            raise AssertionError('obj type %r != Struct or Union'
                                 % type(obj).__name__)
        return o

    @classmethod
    def _make_babel_friendly(cls, data_type, val):
        """Convert a Python object to a type that will pass validation by a
        Babel data type."""
        if val is None:
            return val
        elif isinstance(data_type, Timestamp):
            return datetime.datetime.strptime(val, data_type.format)
        elif isinstance(data_type, Binary):
            return base64.b64decode(val)
        else:
            return val
