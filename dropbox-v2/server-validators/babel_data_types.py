"""
Defines all of Babel's primitive types in Python. Also provides the high-level
classes that should be extended when defining composite data types.

The data types defined here should not be specific to an RPC or serialization
format.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

from abc import ABCMeta, abstractmethod
import datetime
import numbers
import re
import six
import types

class DataType(object):
    """All primitive and composite data types should extend this."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, val):
        """Validates that val is of this data type.

        Returns: None if validation succeeds.
        Raises: A KeyError or ValueError if validation fails.
        """
        pass

class PrimitiveType(object):
    """A basic type that is defined by Babel."""
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
        if not isinstance(val, six.string_types):
            raise ValueError("'%s' is of type %r and is not a valid string"
                             % (val, type(val).__name__))
        elif self.max_length is not None and len(val) > self.max_length:
            raise ValueError("'%s' must be at most %d characters, got %d"
                             % (val, self.max_length, len(val)))
        elif self.min_length is not None and len(val) < self.min_length:
            raise ValueError("'%s' must be at least %d characters, got %d"
                             % (val, self.min_length, len(val)))
        elif self.pattern and not self.pattern_re.match(val):
            raise ValueError("'%s' did not match pattern '%s'"
                             % (val, self.pattern))

class Binary(PrimitiveType):
    def __init__(self, min_length=None, max_length=None):
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

    def validate(self, val):
        if not isinstance(val, str):
            # TODO: Add support for buffer and file objects.
            raise ValueError("'%s' is of type %r and is not a valid binary type"
                             % (val, type(val).__name__))
        elif self.max_length is not None and len(val) > self.max_length:
            raise ValueError("'%s' must have at most %d bytes, got %d"
                             % (val, self.max_length))
        elif self.min_length is not None and len(val) < self.min_length:
            raise ValueError("'%s' has fewer than %d bytes"
                             % (val, self.min_length))

class Timestamp(PrimitiveType):
    """Note that while a format is specified, it isn't used in validation
    since a native Python datetime object is preferred. The format, however,
    can and should be used by serializers."""

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

class CompositeType(DataType):
    pass

class Struct(CompositeType):
    """
    Extend this when defining a Python class that represents a
    Babel IDL Struct.

    You must specify a _fields_ class variable structured as:
        _fields_ = [(field_name, optional, data_type), ...]

        field_name: Name of the field (str).
        optional: Whether the field is optional (bool).
        data_type: DataType object.
    """
    def validate(self):
        for field_name, optional, data_type in self._fields_:
            # Any absent field that's required will raise an exception
            getattr(self, field_name)

class Union(CompositeType):
    """
    Extend this when defining a Python class that represents a
    Babel IDL Union.

    You must specify a _fields_ class variable structured as:
        _fields_ = [(field_name, data_type), ...]

        field_name: Name of the tag (str).
        data_type: DataType object. None if it's a symbol field.
    """
    def validate(self):
        if self._tag is None:
            raise ValueError('No tag selected')
