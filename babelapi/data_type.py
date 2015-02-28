"""
Defines data types for Babel.

The goal of this module is to define all data types that are common to the
languages and serialization formats we want to support.
"""

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import copy
import datetime
import math
import numbers
import re
import six

class ParameterError(Exception):
    """Raised when a data type is parameterized with a bad type or value."""
    pass

class DataType(object):
    """
    Abstract class representing a data type.

    When extending, use a class name that matches exactly the name you will
    want to use when referencing in a template.
    """

    __metaclass__ = ABCMeta

    # When this is in a context where nullability is relevant, this should be
    # set to True or False.
    nullable = None

    def __init__(self):
        """No-op. Exists so that introspection can be certain that an init
        method exists."""
        pass

    @property
    def name(self):
        """Returns an easy to read name for the type."""
        return self.__class__.__name__

    @abstractmethod
    def check(self, val):
        """
        Checks if val is a valid Python representation for this type. Either
        raises a ValueError or returns None. Return value should be ignored.
        """
        pass

    def __repr__(self):
        return self.name

class PrimitiveType(DataType):
    pass

class Null(PrimitiveType):
    def check(self, val):
        if val is not None:
            raise ValueError('%r is not a valid null type' % val)

class Any(PrimitiveType):
    def check(self, val):
        pass

class Symbol(PrimitiveType):
    def check(self, val):
        raise NotImplemented

class Binary(PrimitiveType):
    def check(self, val):
        if not isinstance(val, str):
            raise ValueError('%r is not valid binary (Python str)' % val)

    @property
    def has_example(self, label):
        return False

    @property
    def get_example(self, label):
        return None

class _BoundedInteger(PrimitiveType):
    """
    When extending, specify 'minimum' and 'maximum' as class variables. This
    is the range of values supported by the data type.
    """
    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            if not isinstance(min_value, numbers.Integral):
                raise ParameterError('min_value must be an integral number')
            if min_value < self.minimum:
                raise ParameterError('min_value cannot be less than the '
                    'minimum value for this type (%s < %s)' %
                    (min_value, self.minimum))
        if max_value is not None:
            if not isinstance(max_value, numbers.Integral):
                raise ParameterError('max_value must be an integral number')
            if max_value > self.maximum:
                raise ParameterError('max_value cannot be greater than the '
                    'maximum value for this type (%s < %s)' %
                    (max_value, self.maximum))
        self.min_value = min_value
        self.max_value = max_value

    def check(self, val):
        if not isinstance(val, numbers.Integral):
            raise ValueError('%r is not a valid integer type' % val)
        if not (self.minimum <= val <= self.maximum):
            raise ValueError('%d is not within range [%r, %r]'
                             % (val, self.minimum, self.maximum))
        if self.min_value is not None and val < self.min_value:
            raise ValueError('%d is less than %d' %
                             (val, self.min_value))
        if self.max_value is not None and val > self.max_value:
            raise ValueError('%d is greater than %d' %
                             (val, self.max_value))

    def __repr__(self):
        return '%s()' % self.name

class Int32(_BoundedInteger):
    minimum = -2**31
    maximum = 2**31 - 1

class UInt32(_BoundedInteger):
    minimum = 0
    maximum = 2**32 - 1

class Int64(_BoundedInteger):
    minimum = -2**63
    maximum = 2**63 - 1

class UInt64(_BoundedInteger):
    minimum = 0
    maximum = 2**64 - 1

class _BoundedFloat(PrimitiveType):
    """
    When extending, optionally specify 'minimum' and 'maximum' as class
    variables. This is the range of values supported by the data type. For
    a float64, there is no need to specify a minimum and maximum since Python's
    native float implementation is a float64/double. Therefore, any Python
    float will pass the data type range check automatically.
    """
    minimum = None
    maximum = None

    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            if not isinstance(min_value, numbers.Real):
                raise ParameterError('min_value must be a real number')
            if not isinstance(min_value, float):
                try:
                    min_value = float(min_value)
                except OverflowError:
                    raise ParameterError('min_value is too small for a float')
            if self.minimum is not None and min_value < self.minimum:
                raise ParameterError('min_value cannot be less than the '
                                     'minimum value for this type (%f < %f)' %
                                     (min_value, self.minimum))
        if max_value is not None:
            if not isinstance(max_value, numbers.Real):
                raise ParameterError('max_value must be a real number')
            if not isinstance(max_value, float):
                try:
                    max_value = float(max_value)
                except OverflowError:
                    raise ParameterError('max_value is too large for a float')
            if self.maximum is not None and max_value > self.maximum:
                raise ParameterError('max_value cannot be greater than the '
                                     'maximum value for this type (%f < %f)' %
                                     (max_value, self.maximum))
        self.min_value = min_value
        self.max_value = max_value

    def check(self, val):
        if not isinstance(val, numbers.Real):
            raise ValueError('%r is not a valid real number' % val)
        if not isinstance(val, float):
            try:
                val = float(val)
            except OverflowError:
                raise ValueError('%r is too large for float' % val)
        if math.isnan(val) or math.isinf(val):
            raise ValueError('%f values are not supported' % val)
        if self.minimum is not None and val < self.minimum:
            raise ValueError('%f is less than %f' %
                             (val, self.minimum))
        if self.maximum is not None and val > self.maximum:
            raise ValueError('%f is greater than %f' %
                             (val, self.maximum))
        if self.min_value is not None and val < self.min_value:
            raise ValueError('%f is less than %f' %
                             (val, self.min_value))
        if self.max_value is not None and val > self.max_value:
            raise ValueError('%f is greater than %f' %
                             (val, self.min_value))

    def __repr__(self):
        return '%s()' % self.name

class Float32(_BoundedFloat):
    # Maximum and minimums from the IEEE 754-1985 standard
    minimum = -3.40282 * 10**38
    maximum = 3.40282 * 10**38

class Float64(_BoundedFloat):
    pass

class Boolean(PrimitiveType):
    def check(self, val):
        if not isinstance(val, bool):
            raise ValueError('%r is not a valid boolean' % val)

class String(PrimitiveType):
    def __init__(self, min_length=None, max_length=None, pattern=None):
        if min_length is not None:
            if not isinstance(min_length, numbers.Integral):
                raise ParameterError('min_length must be an integral number')
            if min_length < 0:
                raise ParameterError('min_length must be >= 0')
        if max_length is not None:
            if not isinstance(max_length, numbers.Integral):
                raise ParameterError('max_length must be an integral number')
            if max_length < 1:
                raise ParameterError('max_length must be > 0')
        if min_length and max_length:
            if max_length < min_length:
                raise ParameterError('max_length must be >= min_length')

        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.pattern_re = None

        if pattern:
            if not isinstance(pattern, six.string_types):
                raise ParameterError('pattern must be a string')
            try:
                self.pattern_re = re.compile(pattern)
            except re.error as e:
                raise ParameterError(
                    'could not compile regex pattern {!r}: {}'.format(
                        pattern, e.args[0]))

    def check(self, val):
        if not isinstance(val, six.string_types):
            raise ValueError('%r is not a valid string' % val)
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
    """Should support any timestamp format, not just the Dropbox format."""

    def __init__(self, format):
        if not isinstance(format, six.string_types):
            raise ParameterError('format must be a string')
        self.format = format

    def check(self, val):
        if not isinstance(val, six.string_types):
            raise ValueError('Timestamp must be specified as a str')

        # Raises a ValueError if val is the incorrect format
        datetime.datetime.strptime(val, self.format)

class List(DataType):
    """Assumes list contents are homogeneous with respect to types."""

    def __init__(self, data_type, min_items=None, max_items=None):
        self.data_type = data_type

        if min_items is not None and min_items < 0:
            raise ParameterError('min_items must be >= 0')
        if max_items is not None and max_items < 1:
            raise ParameterError('max_items must be > 0')
        if min_items and max_items and max_items < min_items:
            raise ParameterError('max_length must be >= min_length')

        self.min_items = min_items
        self.max_items = max_items

    def check(self, val):
        if not isinstance(val, list):
            raise ValueError('%r is not a valid list' % val)
        elif self.max_items is not None and len(val) > self.max_items:
            raise ValueError('%r has more than %s items'
                             % (val, self.max_items))
        elif self.min_items is not None and len(val) < self.min_items:
            raise ValueError('%r has fewer than %s items'
                             % (val, self.min_items))
        for item in val:
            self.data_type.check(item)

    def has_example(self, label):
        if isinstance(self.data_type, CompositeType):
            return self.data_type.has_example(label)
        else:
            return False

    def get_example(self, label):
        if isinstance(self.data_type, CompositeType):
            return self.data_type.get_example(label)
        else:
            return None

def doc_unwrap(raw_doc):
    """
    Applies two transformations to raw_doc:
    1. N consecutive newlines are converted into N-1 newlines.
    2. A lone newline is converted to a space, which basically unwraps text.

    Returns a new string, or None if the input was None.
    """
    if raw_doc is None:
        return None
    docstring = ''
    consecutive_newlines = 0
    # Remove all leading and trailing whitespace in the documentation block
    for c in raw_doc.strip():
        if c == '\n':
            consecutive_newlines += 1
            if consecutive_newlines > 1:
                docstring += c
        else:
            if consecutive_newlines == 1:
                docstring += ' '
            consecutive_newlines = 0
            docstring += c
    return docstring

class Field(object):
    """
    Represents a field in a composite type.
    """

    def __init__(self,
                 name,
                 data_type,
                 doc):
        """
        Creates a new Field.

        :param str name: Name of the field.
        :param Type data_type: The type of variable for of this field.
        :param str doc: Documentation for the field.
        :param bool deprecated: Whether the field is deprecated.
        """
        self.name = name
        self.data_type = data_type
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)

    def __repr__(self):
        return 'Field(%r, %r)' % (self.name,
                                  self.data_type)

class StructField(Field):
    """
    Represents a field in a composite type.
    """

    def __init__(self,
                 name,
                 data_type,
                 doc,
                 deprecated=False):
        """
        Creates a new Field.

        :param str name: Name of the field.
        :param Type data_type: The type of variable for of this field.
        :param str doc: Documentation for the field.
        :param bool deprecated: Whether the field is deprecated.
        """
        super(StructField, self).__init__(name, data_type, doc)
        self.deprecated = deprecated
        self.has_default = False
        self._default = None

    def set_default(self, default):
        self.has_default = True
        self._default = default

    @property
    def default(self):
        if not self.has_default:
            raise Exception('Type has no default')
        else:
            return self._default

    def check(self, val):
        if val is None:
            if self.data_type.nullable:
                return None
            else:
                raise ValueError('val is None but type is not nullable')
        else:
            return self.data_type.check(val)

    def __repr__(self):
        return 'StructField(%r, %r)' % (self.name,
                                        self.data_type)

class UnionField(Field):
    def __init__(self,
                 name,
                 data_type,
                 doc,
                 catch_all=False):
        super(UnionField, self).__init__(name, data_type, doc)
        self.catch_all = catch_all

class CompositeType(DataType):
    """
    Composite types are any data type which can be constructed using primitive
    data types and other composite types.
    """

    DEFAULT_EXAMPLE_LABEL = 'default'

    def __init__(self, name, doc, fields):
        """
        Creates a CompositeType.

        Fields are specified as a list so that order is preserved for display
        purposes only. (Might be used for certain serialization formats...)

        :param str name: Name of type.
        :param str doc: Description of type.
        :param list(Field) fields: Ordered list of fields for type.
        :param dict example: An example of the type as a JSON-compatible dict.
        """
        self._name = name
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)
        self.fields = fields
        self.examples = {}

    @property
    def name(self):
        return self._name

    @abstractmethod
    def get_example(self, label, example):
        pass

    @abstractmethod
    def add_example(self, label, text, example):
        pass

    def copy(self):
        return copy.deepcopy(self)

    def prepend_field(self, field):
        self.fields.insert(0, field)

class OrderedExample(OrderedDict):

    def __init__(self, *args, **kwargs):
        super(OrderedExample, self).__init__(*args, **kwargs)
        self.text = None

class Struct(CompositeType):
    """
    Defines a product type: Composed of other primitive and/or struct types.
    """

    composite_type = 'struct'

    def __init__(self, name, doc, fields, supertype=None, coverage_names=None):
        """
        :param Struct supertype: If this should subtype another.
        """
        super(Struct, self).__init__(name, doc, fields)
        self.coverage_names = coverage_names
        self.coverage = []
        self.supertype = supertype

    def has_coverage(self):
        return bool(self.coverage_names)

    def resolve_coverage(self, env):
        """
        Struct is defined before types that it covers are defined. So use an
        env to resolve the name of those data types into data type objects.
        """
        for coverage_name in self.coverage_names:
            if coverage_name in env:
                data_type = env[coverage_name]
                if data_type.supertype is None:
                    raise ValueError('All coverage must be subtypes of %r'
                                     % self.name)
                if data_type.supertype != self:
                    raise ValueError('All coverage must subtype %r not %r'
                                     % (self.name, data_type.supertype.name))
                self.coverage.append(data_type)
            else:
                raise KeyError('No data type named %s' % coverage_name)

    def check(self, val):
        # Enforce the existence of all fields
        if not isinstance(val, dict):
            raise ValueError('val must be a dict')

        for field in self.fields:
            if field.name in val:
                field.check(val[field.name])
            else:
                raise ValueError('Field %r is unspecified' % field.name)

    @property
    def all_fields(self):
        """
        Returns an iterator of all fields. Required fields before optional
        fields. Super type fields before type fields.
        """
        return self.all_required_fields + self.all_optional_fields

    def _filter_fields(self, filter_function):
        """
        Utility to iterate through all fields (super types first) of a type.

        :param filter: A function that takes in a Field object. If it returns
            True, the field is part of the generated output. If False, it is
            omitted.
        """
        fields = []
        if self.supertype:
            fields.extend(self.supertype._filter_fields(filter_function))
        fields.extend(filter(filter_function, self.fields))
        return fields

    @property
    def all_required_fields(self):
        """
        Returns an iterator that traverses required fields in all super types
        first, and then for this type.
        """
        def required_check(f):
            return not f.data_type.nullable and not f.has_default
        return self._filter_fields(required_check)

    @property
    def all_optional_fields(self):
        """
        Returns an iterator that traverses optional fields in all super types
        first, and then for this type.
        """
        def optional_check(f):
            return f.data_type.nullable or f.has_default
        return self._filter_fields(optional_check)

    def add_example(self, label, text, example):
        """
        Add a plausible example of the contents of this type. The example is
        validated against the type definition.

        :param str label: A label for the example.
        :param dict example: An example of the type represented as a dict of a
            subset of Python primitives (str, unicode, list, int/long, float).
        """
        if label in example:
            raise ValueError('Example label %s already specified' % label)

        ordered_example = OrderedExample()
        ordered_example.text = text

        # Check for examples with keys that don't belong
        extra_fields = set(example.keys()) - set([f.name for f in self.all_fields])
        if extra_fields:
            raise KeyError('Example for %r has invalid fields %r'
                           % (self.name, extra_fields))

        for field in self.all_fields:
            if field.name in example:
                if isinstance(field.data_type, CompositeType):
                    # An example that specifies the key as null is okay if the
                    # field permits it.
                    if field.data_type.nullable and example[field.name] is None:
                        ordered_example[field.name] = None
                    else:
                        raise KeyError('Field %r should not be specified since '
                                       'it is a composite type declaration.'
                                       % field.name)
                elif isinstance(field.data_type, List):
                    if isinstance(field.data_type.data_type, CompositeType):
                        raise KeyError('Field %r should not be specified '
                                       'since it is a list of composite '
                                       'types.' % field.name)
                    else:
                        field.check(example[field.name])
                        ordered_example[field.name] = example[field.name]
                else:
                    field.check(example[field.name])
                    ordered_example[field.name] = example[field.name]
            elif not isinstance(field.data_type, (CompositeType, List)) \
                    and not field.data_type.nullable:
                raise KeyError('Missing field %r in example' % field.name)
        self.examples[label] = ordered_example

    def has_example(self, label):
        return label in self.examples

    def get_example(self, label):
        example = self.examples.get(label)
        if example is None:
            return None
        else:
            example_copy = copy.copy(example)
            for field in self.all_fields:
                if field.name in example_copy:
                    # Only valid when the field has been set to null in the
                    # example.
                    continue
                elif isinstance(field.data_type, CompositeType):
                    if field.data_type.has_example(label):
                        example_copy[field.name] = field.data_type.get_example(label)
                    elif field.data_type.has_example(self.DEFAULT_EXAMPLE_LABEL):
                        example_copy[field.name] = field.data_type.get_example(
                            self.DEFAULT_EXAMPLE_LABEL,
                        )
                    else:
                        raise Exception('No example with label %r for subtype '
                                        '%r' % (label, field.data_type.name))
                elif (isinstance(field.data_type, List) and
                        isinstance(field.data_type.data_type, CompositeType)):
                    example_copy[field.name] = [field.data_type.data_type.get_example(label)]
            return example_copy

    def __repr__(self):
        return 'Struct(%r, %r)' % (self.name, self.fields)

class Union(CompositeType):
    """Defines a tagged union. Fields are variants."""

    composite_type = 'union'

    def __init__(self, name, doc, fields, subtype=None, catch_all_field=None):
        """
        :param Union subtype: If this should supertype another.
        """
        super(Union, self).__init__(name, doc, fields)
        self.catch_all_field = catch_all_field
        self.subtype = subtype

    def check(self, val):
        if not isinstance(val, TagRef):
            raise ValueError('%r is not a tag of %s' % (val, self.name))
        for field in self.all_fields:
            if val.tag_name == field.name:
                if not is_symbol_type(field.data_type):
                    raise ValueError('invalid tag reference to non-symbol %r' %
                                     val.tag_name)
                return None
        else:
            raise ValueError('unknown tag %r for %s' % (val.tag_name, self.name))

    @property
    def all_fields(self):
        """
        Returns a list of all fields. Subtype fields come before this type's
        fields.
        """
        fields = []
        if self.subtype:
            fields.extend(self.subtype.all_fields)
        fields.extend([f for f in self.fields])
        return fields

    def has_example(self, label):
        for field in self.fields:
            if (isinstance(field, Field)
                    and isinstance(field.data_type, CompositeType)
                    and field.data_type.has_example(label)):

                return True
        else:
            for field in self.fields:
                if is_symbol_type(field.data_type) and field.name == label:
                    return True

            return False
        return False

    def get_example(self, label):
        for field in self.fields:
            if (isinstance(field, Field)
                    and isinstance(field.data_type, CompositeType)
                    and field.data_type.has_example(label)):
                return {field.name: field.data_type.get_example(label)}
        else:
            # Fallback to checking for direct symbols
            for field in self.fields:
                if is_symbol_type(field.data_type) and field.name == label:
                    return field.name
            else:
                return None

    def add_example(self, label, example):
        raise NotImplemented

    def unique_field_data_types(self):
        """
        Checks if all variants have different data types.

        If so, the selected variant can be determined just by the data type of
        the value without needing a field name / tag. In some languages, this
        lets us make a shortcut
        """
        data_type_names = set()
        for field in self.fields:
            if not is_symbol_type(field.data_type):
                if field.data_type.name in data_type_names:
                    return False
                else:
                    data_type_names.add(field.data_type.name)
        else:
            return True

    def __repr__(self):
        return 'Union(%r, %r)' % (self.name, self.fields)

class TagRef(object):
    """
    Used when an ID in Babel refers to a tag of a union.
    TODO(kelkabany): Support tag values.
    """

    def __init__(self, union_data_type, tag_name):
        self.union_data_type = union_data_type
        self.tag_name = tag_name

    def __repr__(self):
        return 'TagRef(%r, %r)' % (self.union_data_type, self.tag_name)

Empty = Struct('Empty', None, [])

def is_any_type(data_type):
    return isinstance(data_type, Any)
def is_binary_type(data_type):
    return isinstance(data_type, Binary)
def is_boolean_type(data_type):
    return isinstance(data_type, Boolean)
def is_composite_type(data_type):
    return isinstance(data_type, CompositeType)
def is_integer_type(data_type):
    return isinstance(data_type, (UInt32, UInt64, Int32, Int64))
def is_empty(data_type):
    return data_type == Empty
def is_float_type(data_type):
    return isinstance(data_type, (Float32, Float64))
def is_list_type(data_type):
    return isinstance(data_type, List)
def is_null_type(data_type):
    return isinstance(data_type, Null)
def is_numeric_type(data_type):
    return is_integer_type(data_type) or is_float_type(data_type)
def is_primitive_type(data_type):
    return isinstance(data_type, PrimitiveType)
def is_string_type(data_type):
    return isinstance(data_type, String)
def is_symbol_type(data_type):
    return isinstance(data_type, Symbol)
def is_struct_type(data_type):
    return isinstance(data_type, Struct)
def is_tag_ref(val):
    return isinstance(val, TagRef)
def is_timestamp_type(data_type):
    return isinstance(data_type, Timestamp)
def is_union_type(data_type):
    return isinstance(data_type, Union)
