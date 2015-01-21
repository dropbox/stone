"""
Defines classes to represent each Babel type in Python. These classes should
be used to validate Python objects and normalize them for a given type.

The data types defined here should not be specific to an RPC or serialization
format.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.

EDITING THIS FILE? Please modify the version in the babelapi repo,
"""

from abc import ABCMeta, abstractmethod
import datetime
import numbers
import re
import six

if six.PY3:
    _binary_types = (bytes, memoryview)
else:
    _binary_types = (bytes, buffer)

class ValidationError(Exception):
    pass

def generic_type_name(v):
    """Return a descriptive type name that isn't Python specific. For example,
    an int value will return 'integer' rather than 'int'."""
    if isinstance(v, numbers.Integral):
        # Must come before real numbers check since integrals are reals too
        return 'integer'
    elif isinstance(v, numbers.Real):
        return 'float'
    elif isinstance(v, (tuple, list)):
        return 'list'
    elif isinstance(v, six.string_types):
        return 'string'
    else:
        return type(v).__name__

class Validator(object):
    """All primitive and composite data types should be a subclass of this."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, val):
        """Validates that val is of this data type.

        Returns: A normalized value if validation succeeds.
        Raises: ValidationError
        """
        pass

class PrimitiveType(Validator):
    """A basic type that is defined by Babel."""
    pass

class Boolean(PrimitiveType):
    def validate(self, val):
        if not isinstance(val, bool):
            raise ValidationError('%r is not a valid boolean' % val)
        return val

class Integer(PrimitiveType):
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
            assert isinstance(min_value, numbers.Integral), \
                'min_value must be an integral number'
            if min_value < self.minimum:
                raise ValueError('min_value cannot be less than the minimum '
                                 'value for this type (%d < %d)'
                                 % (min_value, self.minimum))
            self.minimum = min_value
        if max_value is not None:
            assert isinstance(max_value, numbers.Integral), \
                'max_value must be an integral number'
            if max_value > self.maximum:
                raise ValueError('max_value cannot be greater than the maximum '
                                 'value for this type (%d < %d)'
                                 % (max_value, self.maximum))
            self.maximum = max_value

    def validate(self, val):
        if not isinstance(val, numbers.Integral):
            raise ValidationError('expected integer, got %s'
                                  % generic_type_name(val))
        elif not (self.minimum <= val <= self.maximum):
            raise ValidationError('%d is not within range [%d, %d]'
                                  % (val, self.minimum, self.maximum))
        return val

    def __repr__(self):
        return '%s()' % self.__class__.__name__

class Int32(Integer):
    minimum = -2**31
    maximum = 2**31 - 1

class UInt32(Integer):
    minimum = 0
    maximum = 2**32 - 1

class Int64(Integer):
    minimum = -2**63
    maximum = 2**63 - 1

class UInt64(Integer):
    minimum = 0
    maximum = 2**64 - 1

class String(PrimitiveType):
    """Represents a unicode string."""
    def __init__(self, min_length=None, max_length=None, pattern=None):
        if min_length is not None:
            assert isinstance(min_length, numbers.Integral), \
                'min_length must be an integral number'
            assert min_length >= 0, 'min_length must be >= 0'
        if max_length is not None:
            assert isinstance(max_length, numbers.Integral), \
                'max_length must be an integral number'
            assert max_length > 0, 'max_length must be > 0'
        if min_length and max_length:
            assert max_length >= min_length, 'max_length must be >= min_length'
        if pattern is not None:
            assert isinstance(pattern, six.string_types), \
                'pattern must be a string'

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
        """
        A unicode string of the correct length and pattern will pass validation.
        In PY2, we enforce that a str type must be valid utf-8, and a unicode
        string will be returned.
        """
        if not isinstance(val, six.string_types):
            raise ValidationError("'%s' expected to be a string, got %s"
                                  % (val, generic_type_name(val)))
        if not six.PY3 and isinstance(val, str):
            try:
                val = val.decode('utf-8')
            except UnicodeDecodeError:
                raise ValidationError("'%s' was not valid utf-8")

        if self.max_length is not None and len(val) > self.max_length:
            raise ValidationError("'%s' must be at most %d characters, got %d"
                                  % (val, self.max_length, len(val)))
        if self.min_length is not None and len(val) < self.min_length:
            raise ValidationError("'%s' must be at least %d characters, got %d"
                                  % (val, self.min_length, len(val)))

        if self.pattern and not self.pattern_re.match(val):
            raise ValidationError("'%s' did not match pattern '%s'"
                                  % (val, self.pattern))
        return val

class Binary(PrimitiveType):
    def __init__(self, min_length=None, max_length=None):
        if min_length is not None:
            assert isinstance(min_length, numbers.Integral), \
                'min_length must be an integral number'
            assert min_length >= 0, 'min_length must be >= 0'
        if max_length is not None:
            assert isinstance(max_length, numbers.Integral), \
                'max_length must be an integral number'
            assert max_length > 0, 'max_length must be > 0'
        if min_length is not None and max_length is not None:
            assert max_length >= min_length, 'max_length must be >= min_length'

        self.min_length = min_length
        self.max_length = max_length

    def validate(self, val):
        if not isinstance(val, _binary_types):
            raise ValidationError("expected binary type, got %s"
                                  % generic_type_name(val))
        elif self.max_length is not None and len(val) > self.max_length:
            raise ValidationError("'%s' must have at most %d bytes, got %d"
                                  % (val, self.max_length, len(val)))
        elif self.min_length is not None and len(val) < self.min_length:
            raise ValidationError("'%s' has fewer than %d bytes, got %d"
                                  % (val, self.min_length, len(val)))
        return val

class Timestamp(PrimitiveType):
    """Note that while a format is specified, it isn't used in validation
    since a native Python datetime object is preferred. The format, however,
    can and should be used by serializers."""

    def __init__(self, format):
        """format must be composed of format codes that the C standard (1989)
        supports, most notably in its strftime() function."""
        assert isinstance(format, str), 'format must be a string'
        self.format = format

    def validate(self, val):
        if not isinstance(val, datetime.datetime):
            raise ValidationError('expected timestamp, got %s'
                                  % generic_type_name(val))
        elif val.tzinfo is not None:
            raise ValidationError('timestamp should not have a timezone set')
        return val

class List(PrimitiveType):
    """Assumes list contents are homogeneous with respect to types."""

    def __init__(self, item_data_type, min_items=None, max_items=None):
        """Every list item will be validated with item_data_type."""
        self.item_data_type = item_data_type
        if min_items is not None:
            assert isinstance(min_items, numbers.Integral), \
                'min_items must be an integral number'
            assert min_items >= 0, 'min_items must be >= 0'
        if max_items is not None:
            assert isinstance(max_items, numbers.Integral), \
                'max_items must be an integral number'
            assert max_items > 0, 'max_items must be > 0'
        if min_items is not None and max_items is not None:
            assert max_items >= min_items, 'max_items must be >= min_items'

        self.min_items = min_items
        self.max_items = max_items

    def validate(self, val):
        if not isinstance(val, (tuple, list)):
            raise ValidationError('%r is not a valid list' % val)
        elif self.max_items is not None and len(val) > self.max_items:
            raise ValidationError('%r has more than %s items'
                                  % (val, self.max_items))
        elif self.min_items is not None and len(val) < self.min_items:
            raise ValidationError('%r has fewer than %s items'
                                  % (val, self.min_items))
        return [self.item_data_type.validate(item) for item in val]

class CompositeType(Validator):
    def __init__(self, definition):
        """
        definition must have a _fields_ attribute with the following structure:

            _fields_ = [(field_name, data_type), ...]

            field_name: Name of the field (str).
            data_type: Validator object.
        """
        assert hasattr(definition, '_fields_'), 'needs _fields_ attribute'
        self.definition = definition
    def validate_type_only(self, val):
        """Use this when you only want to validate that the type of an object
        is correct, but not yet validate each field."""
        if type(val) is not self.definition:
            raise ValidationError('expected type %s, got %s'
                % (self.definition.__name__, generic_type_name(val)))

class Struct(CompositeType):
    def validate(self, val):
        """
        For a val to pass validation, each required field must be present as
        an object attribute. This assumes that each field has already been
        validated by the object, so it does not explicitly check them.
        """
        self.validate_type_only(val)
        for field_name, _ in self.definition._fields_:
            if not hasattr(val, field_name):
                raise ValidationError("missing required field '%s'" %
                                      field_name)
        return val

class Union(CompositeType):
    def validate(self, val):
        """
        For a val to pass validation, it must have a _tag set. This assumes
        that the object validated that _tag is a valid tag, and that any
        associated value has also been validated.
        """
        self.validate_type_only(val)
        if not hasattr(val, '_tag') or val._tag is None:
            raise ValidationError('no tag set')
        return val

class Any(Validator):
    """
    A special type that accepts any value. Only valid as the data type of a
    union variant.
    """
    def validate(self, val):
        return val

class Symbol(Validator):
    """
    Only valid as the data type of a union variant. This type should be thought
    of as a value-less variant.
    """
    def validate(self, val):
        raise AssertionError('No value validates as a symbol.')

class FunctionStyle(object):
    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return "FunctionStyle.{}".format(self.ident)

FunctionStyle.RPC = FunctionStyle("RPC")
FunctionStyle.UPLOAD = FunctionStyle("UPLOAD")
FunctionStyle.DOWNLOAD = FunctionStyle("DOWNLOAD")

class FunctionSignature(object):
    def __init__(self, style, request_type, response_type, error_type):
        self.style = style
        self.request_type = request_type
        self.response_type = response_type
        self.error_type = error_type

    def __repr__(self):
        return "FunctionSignature{!r}".format((
            self.style, self.request_type, self.response_type, self.error_type))
