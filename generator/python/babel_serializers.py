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
    if isinstance(data_type, bv.List):
        # Because Lists are mutable, we always validate them during
        # serialization.
        obj = data_type.validate(obj)
        return [_json_encode_helper(data_type.item_validator, item)
                for item in obj]
    elif isinstance(data_type, bv.Nullable):
        if needs_validation:
            obj = data_type.validate(obj)
        return (_json_encode_helper(data_type.validator, obj, False)
                if obj is not None else None)
    elif isinstance(data_type, bv.Primitive):
        if needs_validation:
            obj = data_type.validate(obj)
        return _make_json_friendly(data_type, obj)
    elif isinstance(data_type, bv.Struct):
        d = collections.OrderedDict()
        if needs_validation:
            data_type.validate_type_only(obj)
        for field_name, field_data_type in data_type.definition._fields_:
            try:
                val = getattr(obj, field_name)
            except AttributeError as e:
                raise bv.ValidationError(e.args[0])
            presence_key = '_%s_present' % field_name
            if val is not None and getattr(obj, presence_key):
                # This check makes sure that we don't serialize absent struct
                # fields as null, even if there is a default.
                d[field_name] = _json_encode_helper(field_data_type, val, False)
        return d
    elif isinstance(data_type, bv.Union):
        if needs_validation:
            data_type.validate_type_only(obj)
        if obj._tag is None:
            raise bv.ValidationError('no tag set')
        field_data_type = data_type.definition._tagmap_[obj._tag]
        if field_data_type is not None:
            if isinstance(field_data_type, (bv.Any, bv.Symbol)):
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
    """
    try:
        deserialized_obj = json.loads(serialized_obj)
    except ValueError:
        raise bv.ValidationError('could not decode input as JSON')
    else:
        return _json_decode_helper(data_type, deserialized_obj, strict)

def _json_decode_helper(data_type, obj, strict, validate_primitives=True):
    """
    Decodes a JSON-compatible object based on its data type into a
    representative Python object.

    See json_decode() for argument descriptions.

    Args:
        validate_primitives (bool): Whether primitives should be validated.
            This is an efficiency optimization since struct fields and union
            values are already validated on assignment, and don't need to be
            re-validated.
    """
    if isinstance(data_type, bv.Struct):
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
                v = _json_decode_helper(field_data_type, obj[name], strict, False)
                setattr(o, name, v)
        data_type.validate(o)
    elif isinstance(data_type, bv.Union):
        val = None  # Symbols do not have values
        if isinstance(obj, six.string_types):
            # Variant is a symbol
            tag = obj
            if tag in data_type.definition._tagmap_:
                val_data_type = data_type.definition._tagmap_[tag]
                if not isinstance(val_data_type, (bv.Any, bv.Symbol)):
                    raise bv.ValidationError(
                        "expected object for '%s', got symbol" % tag)
            else:
                if not strict and data_type.definition._catch_all_:
                    tag = data_type.definition._catch_all_
                else:
                    raise bv.ValidationError("unknown tag '%s'" % tag)
        elif isinstance(obj, dict):
            # Variant is not a symbol
            if len(obj) != 1:
                raise bv.ValidationError('expected 1 key, got %s', len(obj))
            tag = list(obj)[0]
            raw_val = obj[tag]
            if tag in data_type.definition._tagmap_:
                val_data_type = data_type.definition._tagmap_[tag]
                if isinstance(val_data_type, bv.Symbol):
                    raise bv.ValidationError("expected symbol '%s', got object"
                                             % tag)
                elif not isinstance(val_data_type, bv.Any):
                    val = _json_decode_helper(val_data_type, raw_val, strict, False)
            else:
                if not strict and data_type.definition._catch_all_:
                    tag = data_type.definition._catch_all_
                else:
                    raise bv.ValidationError("unknown tag '%s'" % tag)
        else:
            raise bv.ValidationError("expected string or object, got %s" %
                                     bv.generic_type_name((obj)))
        o = data_type.definition(tag, val)
    elif isinstance(data_type, bv.List):
        if not isinstance(obj, list):
            raise bv.ValidationError(
                'expected list, got %s' %
                bv.generic_type_name(obj)
            )
        return [_json_decode_helper(data_type.item_validator, item, strict)
                for item in obj]
    elif isinstance(data_type, bv.Nullable):
        if obj is not None:
            return _json_decode_helper(data_type.validator, obj, strict)
        else:
            return None
    elif isinstance(data_type, bv.Primitive):
        return _make_babel_friendly(data_type, obj, validate_primitives)
    else:
        raise AssertionError('Cannot handle type %r.'
                             % data_type)
    return o

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
