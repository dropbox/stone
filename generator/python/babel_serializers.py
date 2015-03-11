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
    from . import babel_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import babel_validators as bv

# --------------------------------------------------------------
# JSON Encoder

def json_encode(data_type, obj):
    """Encodes an object into JSON based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.

    Returns:
        str: JSON-encoded object.

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
    return json.dumps(json_compat_obj_encode(data_type, obj))

def json_compat_obj_encode(data_type, obj):
    """Encodes an object into a JSON-compatible dict based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.

    Returns:
        An object that when passed to json.dumps() will produce a string
        giving the JSON-encoded object.

    See json_encode() for additional information about validation.
    """
    if isinstance(data_type, (bv.Struct, bv.Union)):
        # Only validate the type because fields are validated on assignment.
        data_type.validate_type_only(obj)
    else:
        data_type.validate(obj)
    return _json_compat_obj_encode_helper(data_type, obj)

def _json_compat_obj_encode_helper(data_type, obj):
    """
    See json_encode() for argument descriptions.
    """
    if isinstance(data_type, bv.List):
        return _encode_list(data_type, obj)
    elif isinstance(data_type, bv.Nullable):
        return _encode_nullable(data_type, obj)
    elif isinstance(data_type, bv.Primitive):
        return _make_json_friendly(data_type, obj)
    elif isinstance(data_type, bv.Struct):
        return _encode_struct(data_type, obj)
    elif isinstance(data_type, bv.Union):
        return _encode_union(data_type, obj)
    else:
        raise AssertionError('Unsupported data type %r' %
                             type(data_type).__name__)

def _encode_list(data_type, obj):
    """
    The data_type argument must be a List.
    See json_encode() for argument descriptions.
    """
    # Because Lists are mutable, we always validate them during serialization.
    obj = data_type.validate(obj)
    return [_json_compat_obj_encode_helper(data_type.item_validator, item)
            for item in obj]

def _encode_nullable(data_type, obj):
    """
    The data_type argument must be a Nullable.
    See json_encode() for argument descriptions.
    """
    if obj is not None:
        return _json_compat_obj_encode_helper(data_type.validator, obj)
    else:
        return None

def _encode_struct(data_type, obj):
    """
    The data_type argument must be a Struct.
    See json_encode() for argument descriptions.
    """
    # We skip validation of fields with primitive data types in structs and
    # unions because they've already been validated on assignment.
    d = collections.OrderedDict()
    for field_name, field_data_type in data_type.definition._fields_:
        try:
            val = getattr(obj, field_name)
        except AttributeError as e:
            raise bv.ValidationError(e.args[0])
        presence_key = '_%s_present' % field_name
        if val is not None and getattr(obj, presence_key):
            # This check makes sure that we don't serialize absent struct
            # fields as null, even if there is a default.
            try:
                d[field_name] = _json_compat_obj_encode_helper(
                    field_data_type, val)
            except bv.ValidationError as e:
                e.add_parent(field_name)
                raise
    return d

def _encode_union(data_type, obj):
    """
    The data_type argument must be a Union.
    See json_encode() for argument descriptions.
    """
    if obj._tag is None:
        raise bv.ValidationError('no tag set')
    field_data_type = data_type.definition._tagmap[obj._tag]
    if field_data_type is None:
        return obj._tag
    else:
        if (isinstance(field_data_type, (bv.Any, bv.Symbol)) or
                (isinstance(field_data_type, bv.Nullable) and
                 obj._value is None)):
            return obj._tag
        else:
            try:
                encoded_val = _json_compat_obj_encode_helper(
                    field_data_type, obj._value)
            except bv.ValidationError as e:
                e.add_parent(obj._tag)
                raise
            else:
                return {obj._tag: encoded_val}

def _make_json_friendly(data_type, val):
    """
    Convert a primitive type to a Python type that can be serialized by the
    json package.
    """
    if isinstance(data_type, bv.Timestamp):
        return val.strftime(data_type.format)
    elif isinstance(data_type, bv.Binary):
        return base64.b64encode(val)
    elif isinstance(data_type, bv.Integer) and isinstance(val, bool):
        # A bool is a subclass of an int so it passes Integer validation. But,
        # we want the bool to be encoded as an Integer (1/0) rather than T/F.
        return int(val)
    else:
        return val

# --------------------------------------------------------------
# JSON Decoder

def json_decode(data_type, serialized_obj, strict=True):
    """Performs the reverse operation of json_encode.

    Args:
        data_type (Validator): Validator for serialized_obj.
        serialized_obj (str): The JSON string to deserialize.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. strict should only be used by a
            recipient of serialized JSON if it's guaranteed that its Babel
            specs are at least as recent as the senders it receives messages
            from.

    Returns:
        The returned object depends on the input data_type.
            - Binary -> bytes
            - Boolean -> bool
            - Float -> float
            - Integer -> long
            - List -> list
            - Nullable -> None or its wrapped type.
            - String -> unicode (PY2) or str (PY3)
            - Struct -> An instance of its definition attribute.
            - Timestamp -> datetime.datetime
            - Union -> An instance of its definition attribute.
    """
    try:
        deserialized_obj = json.loads(serialized_obj)
    except ValueError:
        raise bv.ValidationError('could not decode input as JSON')
    else:
        return json_compat_obj_decode(data_type, deserialized_obj, strict)

def json_compat_obj_decode(data_type, obj, strict=True):
    """
    Decodes a JSON-compatible object based on its data type into a
    representative Python object.

    Args:
        data_type (Validator): Validator for serialized_obj.
        obj: The JSON-compatible object to decode based on data_type.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. See json_decode() for more.

    Returns:
        See json_decode().
    """
    if isinstance(data_type, bv.Primitive):
        return _make_babel_friendly(data_type, obj, True)
    else:
        return _json_compat_obj_decode_helper(data_type, obj, strict)

def _json_compat_obj_decode_helper(data_type, obj, strict):
    """
    See json_compat_obj_decode() for argument descriptions.
    """
    if isinstance(data_type, bv.Struct):
        o = _decode_struct(data_type, obj, strict)
    elif isinstance(data_type, bv.Union):
        o = _decode_union(data_type, obj, strict)
    elif isinstance(data_type, bv.List):
        o = _decode_list(data_type, obj, strict)
    elif isinstance(data_type, bv.Nullable):
        o = _decode_nullable(data_type, obj, strict)
    elif isinstance(data_type, bv.Primitive):
        return _make_babel_friendly(data_type, obj, False)
    else:
        raise AssertionError('Cannot handle type %r.' % data_type)
    return o

def _decode_struct(data_type, obj, strict):
    """
    The data_type argument must be a Struct.
    See json_compat_obj_decode() for argument descriptions.
    """
    if not isinstance(obj, dict):
        raise bv.ValidationError('expected object, got %s' %
                                 bv.generic_type_name(obj))
    if strict:
        for key in obj:
            if key not in data_type.definition._field_names_:
                raise bv.ValidationError("unknown field '%s'" % key)
    o = data_type.definition()
    for name, field_data_type in data_type.definition._fields_:
        if name in obj:
            if obj[name] is None:
                raise bv.ValidationError("field '%s' has null value" % key)
            try:
                v = _json_compat_obj_decode_helper(
                    field_data_type, obj[name], strict)
                setattr(o, name, v)
            except bv.ValidationError as e:
                e.add_parent(name)
                raise
    # Check that all required fields have been set.
    data_type.validate_fields_only(o)
    return o

def _decode_union(data_type, obj, strict):
    """
    The data_type argument must be a Union.
    See json_compat_obj_decode() for argument descriptions.
    """
    val = None  # Symbols do not have values
    if isinstance(obj, six.string_types):
        # Union member has no associated value
        tag = obj
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if not isinstance(val_data_type, (bv.Any, bv.Symbol, bv.Nullable)):
                raise bv.ValidationError(
                    "expected object for '%s', got symbol" % tag)
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    elif isinstance(obj, dict):
        # Union member has value
        if len(obj) != 1:
            raise bv.ValidationError('expected 1 key, got %s', len(obj))
        tag = list(obj)[0]
        raw_val = obj[tag]
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if isinstance(val_data_type, bv.Nullable) and raw_val is None:
                raise bv.ValidationError(
                    "expected string '%s', got object with null value" % tag)
            elif isinstance(val_data_type, bv.Symbol):
                raise bv.ValidationError("expected symbol '%s', got object" %
                                         tag)
            elif not isinstance(val_data_type, bv.Any):
                try:
                    val = _json_compat_obj_decode_helper(
                        val_data_type, raw_val, strict)
                except bv.ValidationError as e:
                    e.add_parent(tag)
                    raise
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    else:
        raise bv.ValidationError("expected string or object, got %s" %
                                 bv.generic_type_name(obj))
    return data_type.definition(tag, val)

def _decode_list(data_type, obj, strict):
    """
    The data_type argument must be a List.
    See json_compat_obj_decode() for argument descriptions.
    """
    if not isinstance(obj, list):
        raise bv.ValidationError(
            'expected list, got %s' % bv.generic_type_name(obj))
    return [_json_compat_obj_decode_helper(data_type.item_validator,
                                           item, strict)
            for item in obj]

def _decode_nullable(data_type, obj, strict):
    """
    The data_type argument must be a Nullable.
    See json_compat_obj_decode() for argument descriptions.
    """
    if obj is not None:
        return _json_compat_obj_decode_helper(data_type.validator, obj, strict)
    else:
        return None

def _make_babel_friendly(data_type, val, validate):
    """
    Convert a Python object to a type that will pass validation by its
    validator.
    """
    if isinstance(data_type, bv.Timestamp):
        try:
            return datetime.datetime.strptime(val, data_type.format)
        except ValueError as e:
            raise bv.ValidationError(e.args[0])
    elif isinstance(data_type, bv.Binary):
        try:
            return base64.b64decode(val)
        except TypeError:
            raise bv.ValidationError('invalid base64-encoded binary')
    else:
        if validate:
            data_type.validate(val)
        return val
