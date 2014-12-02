"""
Basic data types that should be re-usable by all Python code generators.
"""

from abc import ABCMeta, abstractmethod
import datetime
import numbers
import re
import types

class DataType(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, val):
        """Checks if val is a valid value for this type."""
        pass

class PrimitiveType(object):
    pass

class Boolean(PrimitiveType):
    def validate(self, val):
        if not isinstance(val, bool):
            raise ValueError('%r is not a valid boolean' % val)

class _Integer(PrimitiveType):
    """
    Do not use this class directly. Extend it and specify a 'minimum' and
    'maximum' value as class variables for the more restrictive integer range.
    """
    minimum = None
    maximum = None

    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            assert isinstance(max_value, numbers.Integral), (
                'min_value must be an integral number'
            )
            if min_value < self.minimum:
                raise ValueError('min_value cannot be less than the minimum '
                                 'value for this type (%s < %s)'
                                 % (min_value, self.minimum))
        if max_value is not None:
            assert isinstance(max_value, numbers.Integral), (
                'max_value must be an integral number'
            )
            if max_value > self.maximum:
                raise ValueError('max_value cannot be greater than the maximum '
                                 'value for this type (%s < %s)'
                                 % (max_value, self.maximum))
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, val):
        if not isinstance(val, numbers.Integral):
            raise ValueError('%r is of type %r and is not a valid integer type'
                             % (val, type(val)))
        elif not (self.minimum <= val <= self.maximum):
            raise ValueError('%s is not within range [%r, %r]'
                             % (val, self.minimum, self.maximum))

    def __repr__(self):
        return '%s()' % self.__class__.__name__

class Int32(_Integer):
    minimum = -2**31
    maximum = 2**31 - 1

class UInt32(_Integer):
    minimum = 0
    maximum = 2**32 - 1

class Int64(_Integer):
    minimum = -2**63
    maximum = 2**63 - 1

class UInt64(_Integer):
    minimum = 0
    maximum = 2**64 - 1

class String(PrimitiveType):
    def __init__(self, min_length=None, max_length=None, pattern=None):
        if min_length is not None:
            assert isinstance(min_length, numbers.Integral), (
                'min_length must be an integral number'
            )
            assert min_length >= 0, 'min_length must be >= 0'
        if max_length is not None:
            assert isinstance(max_length, numbers.Integral), (
                'max_length must be an integral number'
            )
            assert max_length > 0, 'max_length must be > 0'
        if min_length and max_length:
            assert max_length >= min_length, 'max_length must be >= min_length'

        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.pattern_re = None

        if pattern:
            try:
                self.pattern_re = re.compile(pattern)
            except re.error as e:
                raise ValueError('Regex {!r} failed: {}'.format(pattern, e.args[0]))

    def validate(self, val):
        if not isinstance(val, types.StringTypes):
            raise ValueError('%r is of type %r and is not a valid string'
                             % (val, type(val).__name__))
        elif self.max_length is not None and len(val) > self.max_length:
            raise ValueError('%r has more than %s characters'
                             % (val, self.max_length))
        elif self.min_length is not None and len(val) < self.min_length:
            raise ValueError('%r has fewer than %s characters'
                             % (val, self.min_length))
        elif self.pattern and not self.pattern_re.match(val):
            raise ValueError('%r did not match pattern %r'
                             % (val, self.pattern))

class Timestamp(PrimitiveType):
    def __init__(self, format):
        assert isinstance(format, str), (
            'format must be a string'
        )
        self.format = format

    def validate(self, val):
        if not isinstance(val, datetime.datetime):
            raise ValueError('%r is of type %r and is not a valid timestamp'
                             % (val, type(val).__name__))

class List(PrimitiveType):
    """Assumes list contents are homogeneous with respect to types."""

    def __init__(self, data_type, min_items=None, max_items=None):
        self.data_type = data_type

        if min_items is not None:
            assert min_items >= 0, 'min_items must be >= 0'
        if max_items is not None:
            assert max_items > 0, 'max_items must be > 0'
        if min_items and max_items:
            assert max_items >= min_items, 'max_length must be >= min_length'

        self.min_items = min_items
        self.max_items = max_items

    def validate(self, val):
        if not isinstance(val, types.ListType):
            raise ValueError('%r is not a valid list' % val)
        elif self.max_items is not None and len(val) > self.max_items:
            raise ValueError('%r has more than %s items'
                             % (val, self.max_items))
        elif self.min_items is not None and len(val) < self.min_items:
            raise ValueError('%r has fewer than %s items'
                             % (val, self.min_items))

        if isinstance(self.data_type, DataType):
            for item in val:
                self.data_type.validate(item)
        else:
            for item in val:
                if not isinstance(item, self.data_type):
                    raise TypeError('%r is of type %r rather than %r'
                    % (val, type(item).__name__, self.data_type.__name__))
                item.validate()

class CompositeType(DataType): pass
class Struct(CompositeType): pass
class Union(CompositeType): pass

class JsonCompatDictEncoder(object):
    @classmethod
    def encode(cls, obj, data_type=None):
        """
        Encodes a Babel Struct or Union into a JSON-compatible dictionary.
        """
        assert data_type or isinstance(obj, (Struct, Union)), (
            'No data_type is provided -> obj must be a Struct or Union'
        )
        if isinstance(obj, Struct):
            d = {}
            for name, optional, field_data_type  in obj._fields_:
                val = getattr(obj, name)
                if val is not None:
                    d[name] = cls.encode(val, field_data_type)
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
                    return {obj._tag: cls.encode(val)}
            else:
                return obj._tag
        elif isinstance(data_type, List):
            if not isinstance(obj, list):
                # TODO: We want to say the field name
                raise ValueError(
                    'field is of type $r rather than a list'
                    % (type(obj).__name__)
                )
            return [cls.encode(item, data_type.data_type) for item in obj]
        elif isinstance(data_type, PrimitiveType):
            return cls._make_json_friendly(data_type, obj)
        else:
            raise AssertionError('Unsupported data type %r'
                                 % type(data_type).__name__)


    @classmethod
    def _make_json_friendly(cls, data_type, val):
        if val is None:
            return val
        elif isinstance(data_type, (Timestamp,)):
            return val.strftime(data_type.format)
        else:
            return val

class JsonCompatDictDecoder(object):
    @classmethod
    def decode(cls, data_type, obj):
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
                    if isinstance(field_data_type, PrimitiveType):
                        val = cls._make_babel_friendly(field_data_type, obj[name])
                        setattr(o, name, val)
                    else:
                        setattr(o, name, cls.decode(field_data_type, obj[name]))
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
                setattr(o, tag, cls.decode(data_type._fields_[tag], val))
            else:
                raise AssertionError('obj type %r != str or dict'
                                     % type(obj).__name__)
        else:
            raise AssertionError('obj type %r != Struct or Union'
                                 % type(obj).__name__)
        return o

    @classmethod
    def _make_babel_friendly(cls, data_type, val):
        if val is None:
            return val
        elif isinstance(data_type, (Timestamp,)):
            return datetime.datetime.strptime(val, data_type.format)
        else:
            return val
