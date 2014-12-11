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

try:
    from . import babel_data_types as dt
except:
    # babel_data_types is not a top-level module, but this makes testing easier
    import babel_data_types as dt

class JsonEncoder(object):
    """
    Example of serializing a struct to JSON:

    struct FileRef
       path String
       rev String

    > fr = FileRef()
    > fr.path = 'a/b/c'
    > fr.rev = '1234'
    > JsonEncoder.encode(fr)
    "{'path': 'a/b/c', 'rev': '1234'}"

    Example of serializing a union to JSON:

    union UploadMode
        add
        overwrite
        update FileRef

    > um = UploadMode()
    > um.set_add()
    > JsonEncoder.encode(um)
    '"add"'
    > um.update = fr
    > JsonEncoder.encode(um)
    "{'update': {'path': 'a/b/c', 'rev': '1234'}}"
    """

    @classmethod
    def encode(cls, data_type, obj):
        """
        Encodes a Babel data type into JSON.

        This function is also responsible for doing additional validation that
        wasn't done by the objects themselves:

        1. The passed in obj may not have been validated with data_type yet.
        2. If an object that should be a Struct was assigned to a field, its
           type has been validated, but the presence of all required fields
           hasn't been..
        3. If an object that should be a Union was assigned to a field, whether
           or not a tag has been set has not been validated.
        4. A list may have passed validation initially, but been mutated since.
        """
        data_type.validate(obj)
        return json.dumps(cls._encode_helper(data_type, obj))

    @classmethod
    def _encode_helper(cls, data_type, obj):
        """Encodes a Babel data type into a JSON-compatible dict."""
        if isinstance(data_type, dt.List):
            data_type.validate(obj)
            return [cls._encode_helper(data_type.data_type, item) for item in obj]
        elif isinstance(data_type, dt.PrimitiveType):
            return cls._make_json_friendly(data_type, obj)
        elif isinstance(data_type, dt.Struct):
            d = {}
            data_type.validate(obj)
            for name, field_data_type  in data_type.data_type._fields_:
                val = getattr(obj, name)
                if val is not None:
                    d[name] = cls._encode_helper(field_data_type, val)
            return d
        elif isinstance(data_type, dt.Union):
            data_type.validate(obj)
            field_data_type = data_type.data_type._fields_[obj._tag]
            if field_data_type:
                if isinstance(field_data_type, (dt.Any, dt.Symbol)):
                    # TODO(kelkabany): Perhaps a JSON-serializable Any field
                    # should look like {tag: null}
                    return obj._tag
                elif isinstance(field_data_type, dt.Any):
                    return {obj._tag: None}
                elif isinstance(field_data_type, dt.PrimitiveType):
                    val = getattr(obj, obj._tag)
                    return cls._make_json_friendly(field_data_type, val)
                else:
                    val = getattr(obj, obj._tag)
                    return {obj._tag: cls._encode_helper(field_data_type, val)}
            else:
                return obj._tag
        else:
            raise TypeError('Unsupported data type %r'
                            % type(data_type).__name__)

    @classmethod
    def _make_json_friendly(cls, data_type, val):
        """Convert a primitive type to a Python type that can be serialized
        by the json package."""
        if val is None:
            return val
        elif isinstance(data_type, dt.Timestamp):
            return val.strftime(data_type.format)
        elif isinstance(data_type, dt.Binary):
            return base64.b64encode(val)
        else:
            return val

class JsonDecoder(object):
    """Performs the reverse operation of JsonEncoder."""

    @classmethod
    def decode(cls, data_type, serialized_obj, strict=True):
        """If strict, then unknown keys in serialized_obj will raise an error
        and catch all symbols are never used."""
        try:
            return cls._decode_helper(data_type, json.loads(serialized_obj), strict)
        except ValueError:
            raise dt.ValidationError('could not decode input as JSON')

    @classmethod
    def _decode_helper(cls, data_type, obj, strict):
        """
        Decodes a JSON-compatible object based on its Babel data type into a
        representative Python object.
        """
        if isinstance(data_type, dt.Struct):
            if strict:
                for key in obj:
                    if key not in data_type.data_type._field_names_:
                        raise dt.ValidationError("unknown field '%s'" % key)
            o = data_type.data_type()
            for name, field_data_type in data_type.data_type._fields_:
                if name in obj:
                    v = cls._decode_helper(field_data_type, obj[name], strict)
                    setattr(o, name, v)
            data_type.validate(o)
        elif isinstance(data_type, dt.Union):
            o = data_type.data_type()
            if isinstance(obj, six.string_types):
                # Variant is a symbol
                tag = obj
                if tag in data_type.data_type._fields_:
                    val_data_type = data_type.data_type._fields_[tag]
                    if not isinstance(val_data_type, (dt.Any, dt.Symbol)):
                        raise dt.ValidationError("expected object for '%s', got symbol"
                                                 % tag)
                else:
                    if not strict and data_type.data_type._catch_all_:
                        tag = data_type.data_type._catch_all_
                    else:
                        raise dt.ValidationError("unknown tag '%s'" % tag)
                getattr(o, 'set_' + tag)()
            elif isinstance(obj, dict):
                # Variant is not a symbol
                assert len(obj) == 1, 'only 1 key must be specified'
                tag, val = obj.items()[0]
                if tag in data_type.data_type._fields_:
                    val_data_type = data_type.data_type._fields_[tag]
                    if isinstance(val_data_type, dt.Any):
                        getattr(o, 'set_' + tag)()
                    elif isinstance(val_data_type, dt.Symbol):
                        raise dt.ValidationError("expected symbol '%s', got object"
                                                 % tag)
                    else:
                        v = cls._decode_helper(val_data_type, val, strict)
                        setattr(o, tag, v)
                else:
                    if not strict and data_type.data_type._catch_all_:
                        tag = data_type.data_type._catch_all_
                        getattr(o, 'set_' + tag)()
                    else:
                        raise dt.ValidationError("unknown tag '%s'" % tag)
            else:
                raise AssertionError('expected str or dict, got %r'
                                     % dt.generic_type_name((obj)))
        elif isinstance(data_type, dt.List):
            if not isinstance(obj, list):
                raise dt.ValidationError(
                    'expected list, got %s'
                    % dt.generic_type_name(obj)
                )
            return [cls._decode_helper(data_type.data_type, item, strict)
                    for item in obj]
        elif isinstance(data_type, dt.PrimitiveType):
            return cls._make_babel_friendly(data_type, obj)
        else:
            raise AssertionError('expected Struct or Union, got %r'
                                 % dt.generic_type_name(obj))
        return o

    @classmethod
    def _make_babel_friendly(cls, data_type, val):
        """Convert a Python object to a type that will pass validation by a
        Babel data type."""
        if val is None:
            return val
        elif isinstance(data_type, dt.Timestamp):
            return datetime.datetime.strptime(val, data_type.format)
        elif isinstance(data_type, dt.Binary):
            return base64.b64decode(val)
        else:
            return val
