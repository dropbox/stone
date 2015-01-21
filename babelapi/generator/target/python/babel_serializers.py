"""
Serializers that marshal Babel data types into wire formats.

Currently, only JSON is supported. If possible, serializers should be kept
separate from the RPC format.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.

EDITING THIS FILE? Please modify the version in the babelapi repo,
"""

import base64
import collections
import datetime
import json
import six

try:
    from . import babel_data_types as dt
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import babel_data_types as dt

# --------------------------------------------------------------
# JSON Encoder

def json_encode(data_type, obj):
    """
    Encodes a Babel data type into JSON.

    This function will also do additional validation that wasn't done by the
    objects themselves:

    1. The passed in obj may not have been validated with data_type yet.
    2. If an object that should be a Struct was assigned to a field, its
       type has been validated, but the presence of all required fields
       hasn't been.
    3. If an object that should be a Union was assigned to a field, whether
       or not a tag has been set has not been validated.
    4. A list may have passed validation initially, but been mutated since.

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
    return json.dumps(_json_encode_helper(data_type, obj))

def _json_encode_helper(data_type, obj, needs_validation=True):
    """Encodes a Babel data type into a JSON-compatible dict.

    We skip validation of fields with primitive data types in structs and
    unions because they've already been validated on assignment.
    """
    if isinstance(data_type, dt.List):
        # Because Lists are mutable, we always validate them during
        # serialization.
        data_type.validate(obj)
        return [_json_encode_helper(data_type.item_data_type, item)
                for item in obj]
    elif isinstance(data_type, dt.PrimitiveType):
        if needs_validation:
            data_type.validate(obj)
        return _make_json_friendly(data_type, obj)
    elif isinstance(data_type, dt.Struct):
        d = collections.OrderedDict()
        if needs_validation:
            data_type.validate_type_only(obj)
        for field_name, field_data_type in data_type.definition._fields_:
            try:
                val = getattr(obj, field_name)
            except AttributeError as e:
                raise dt.ValidationError(e.args[0])
            if val is not None:
                d[field_name] = _json_encode_helper(field_data_type, val, False)
        return d
    elif isinstance(data_type, dt.Union):
        if needs_validation:
            data_type.validate_type_only(obj)
        if obj._tag is None:
            raise dt.ValidationError('no tag set')
        field_data_type = data_type.definition._fields_[obj._tag]
        if field_data_type is not None:
            if isinstance(field_data_type, (dt.Any, dt.Symbol)):
                return obj._tag
            else:
                val = getattr(obj, '_'+obj._tag)
                return {obj._tag: _json_encode_helper(field_data_type, val, False)}
        else:
            return obj._tag
    else:
        raise AssertionError('Unsupported data type %r'
                             % type(data_type).__name__)

def _make_json_friendly(data_type, val):
    """Convert a primitive type to a Python type that can be serialized
    by the json package."""
    if isinstance(data_type, dt.Timestamp):
        return val.strftime(data_type.format)
    elif isinstance(data_type, dt.Binary):
        return base64.b64encode(val)
    elif isinstance(data_type, dt.Integer) and isinstance(val, bool):
        # A bool is a subclass of an int so it passes Integer validation. But,
        # we want the bool to be encoded as an Integer (1/0) rather than T/F.
        return int(val)
    else:
        return val

# --------------------------------------------------------------
# JSON Decoder

def json_decode(data_type, serialized_obj, strict=True):
    """
    Performs the reverse operation of json_encode.

    If strict, then unknown struct fields will raise an error, and
    unknown union variants will raise an error even if a catch all field
    is specified. strict should only be used by a recipient of serialized
    JSON if it's guaranteed that its Babel specs are at least as recent as
    the senders it receives messages from.
    """
    try:
        deserialized_obj = json.loads(serialized_obj)
    except ValueError:
        raise dt.ValidationError('could not decode input as JSON')
    else:
        return _json_decode_helper(data_type, deserialized_obj, strict)

def _json_decode_helper(data_type, obj, strict, validate_primitives=True):
    """
    Decodes a JSON-compatible object based on its Babel data type into a
    representative Python object.
    """
    if isinstance(data_type, dt.Struct):
        if not isinstance(obj, dict):
            raise dt.ValidationError('expected object, got %s'
                                     % dt.generic_type_name(obj))
        if strict:
            for key in obj:
                if key not in data_type.definition._field_names_:
                    raise dt.ValidationError("unknown field '%s'" % key)
        o = data_type.definition()
        for name, field_data_type in data_type.definition._fields_:
            if name in obj:
                v = _json_decode_helper(field_data_type, obj[name], strict, False)
                setattr(o, name, v)
        data_type.validate(o)
    elif isinstance(data_type, dt.Union):
        val = None # Symbols do not have values
        if isinstance(obj, six.string_types):
            # Variant is a symbol
            tag = obj
            if tag in data_type.definition._fields_:
                val_data_type = data_type.definition._fields_[tag]
                if not isinstance(val_data_type, (dt.Any, dt.Symbol)):
                    raise dt.ValidationError("expected object for '%s', got symbol"
                                             % tag)
            else:
                if not strict and data_type.definition._catch_all_:
                    tag = data_type.definition._catch_all_
                else:
                    raise dt.ValidationError("unknown tag '%s'" % tag)
        elif isinstance(obj, dict):
            # Variant is not a symbol
            if len(obj) != 1:
                raise dt.ValidationError('expected 1 key, got %s', len(obj))
            tag = list(obj)[0]
            raw_val = obj[tag]
            if tag in data_type.definition._fields_:
                val_data_type = data_type.definition._fields_[tag]
                if isinstance(val_data_type, dt.Symbol):
                    raise dt.ValidationError("expected symbol '%s', got object"
                                             % tag)
                elif not isinstance(val_data_type, dt.Any):
                    val = _json_decode_helper(val_data_type, raw_val, strict, False)
            else:
                if not strict and data_type.definition._catch_all_:
                    tag = data_type.definition._catch_all_
                else:
                    raise dt.ValidationError("unknown tag '%s'" % tag)
        else:
            raise dt.ValidationError("expected string or object, got %s"
                                     % dt.generic_type_name((obj)))
        o = data_type.definition(tag, val)
    elif isinstance(data_type, dt.List):
        if not isinstance(obj, list):
            raise dt.ValidationError(
                'expected list, got %s'
                % dt.generic_type_name(obj)
            )
        return [_json_decode_helper(data_type.item_data_type, item, strict)
                for item in obj]
    elif isinstance(data_type, dt.PrimitiveType):
        return _make_babel_friendly(data_type, obj, validate_primitives)
    else:
        raise AssertionError('Cannot handle type %r.'
                             % data_type)
    return o

def _make_babel_friendly(data_type, val, validate):
    """Convert a Python object to a type that will pass validation by a
    Babel data type."""
    if isinstance(data_type, dt.Timestamp):
        try:
            return datetime.datetime.strptime(val, data_type.format)
        except ValueError as e:
            raise dt.ValidationError(e.args[0])
    elif isinstance(data_type, dt.Binary):
        try:
            return base64.b64decode(val)
        except TypeError:
            raise dt.ValidationError('invalid base64-encoded binary')
    else:
        if validate:
            data_type.validate(val)
        return val
