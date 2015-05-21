"""
Defines data types for Babel.

The goal of this module is to define all data types that are common to the
languages and serialization formats we want to support.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import copy
import datetime
import math
import numbers
import re
import six

from .babel.exception import InvalidSpec
from .babel.parser import BabelExampleRef

class ParameterError(Exception):
    """Raised when a data type is parameterized with a bad type or value."""
    pass

def generic_type_name(v):
    """
    Return a descriptive type name that isn't Python specific. For example, an
    int type will return 'integer' rather than 'int'.
    """
    if isinstance(v, BabelExampleRef):
        return "reference"
    elif isinstance(v, numbers.Integral):
        # Must come before real numbers check since integrals are reals too
        return 'integer'
    elif isinstance(v, numbers.Real):
        return 'float'
    elif isinstance(v, (tuple, list)):
        return 'list'
    elif isinstance(v, six.string_types):
        return 'string'
    elif v is None:
        return 'null'
    else:
        return type(v).__name__

class DataType(object):
    """
    Abstract class representing a data type.

    When extending, use a class name that matches exactly the name you will
    want to use when referencing in a template.
    """

    __metaclass__ = ABCMeta

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

class Nullable(DataType):

    def __init__(self, data_type):
        self.data_type = data_type

    def check(self, val):
        if val is not None:
            return self.data_type.check(val)

class Void(PrimitiveType):

    def check(self, val):
        if val is not None:
            raise ValueError('void type can only be null')

class Binary(PrimitiveType):

    def check(self, val):
        if not isinstance(val, str):
            raise ValueError('%r is not valid binary (Python str)' % val)

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
            raise ValueError('%s is not a valid integer type' %
                             generic_type_name(val))
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
            raise ValueError('%s is not a valid real number' %
                             generic_type_name(val))
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
            raise ValueError('%s is not a valid string' %
                             generic_type_name(val))
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
            raise ValueError('Timestamp must be specified as a string')

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
            raise ValueError('%s is not a valid list' % generic_type_name(val))
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
                 doc,
                 token):
        """
        Creates a new Field.

        :param str name: Name of the field.
        :param Type data_type: The type of variable for of this field.
        :param str doc: Documentation for the field.
        :param token: Raw field definition from the parser.
        :type token: babelapi.babel.parser.BabelField
        """
        self.name = name
        self.data_type = data_type
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)
        self._token = token

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
                 token,
                 deprecated=False):
        """
        Creates a new Field.

        :param str name: Name of the field.
        :param Type data_type: The type of variable for of this field.
        :param str doc: Documentation for the field.
        :param token: Raw field definition from the parser.
        :type token: babelapi.babel.parser.BabelField
        :param bool deprecated: Whether the field is deprecated.
        """
        super(StructField, self).__init__(name, data_type, doc, token)
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

    def __repr__(self):
        return 'StructField(%r, %r)' % (self.name,
                                        self.data_type)

class UnionField(Field):
    def __init__(self,
                 name,
                 data_type,
                 doc,
                 token,
                 catch_all=False):
        super(UnionField, self).__init__(name, data_type, doc, token)
        self.catch_all = catch_all

class CompositeType(DataType):
    """
    Composite types are any data type which can be constructed using primitive
    data types and other composite types.
    """

    DEFAULT_EXAMPLE_LABEL = 'default'

    def __init__(self, name, token):
        """
        When this is instantiated, the type is treated as a forward reference.
        Only when :meth:`set_attributes` is called is the type considered to
        be fully defined.

        :param str name: Name of type
        :param token: Raw type definition from the parser.
        :type token: babelapi.babel.parser.BabelTypeDef
        """
        self._name = name
        self._token = token
        self._is_forward_ref = True

        self.raw_doc = None
        self.doc = None
        self.fields = None
        self._raw_examples = None
        self._examples = None
        self._fields_by_name = None

    def set_attributes(self, doc, fields, parent_type=None):
        """
        Fields are specified as a list so that order is preserved for display
        purposes only. (Might be used for certain serialization formats...)

        :param str doc: Description of type.
        :param list(Field) fields: Ordered list of fields for type.
        :param Optional[CompositeType] parent_type: The type this type inherits
            from.
        """
        self.raw_doc = doc
        self.doc = doc_unwrap(doc)
        self.fields = fields
        self._raw_examples = OrderedDict()
        self._examples = OrderedDict()
        self._fields_by_name = {}  # Dict[str, Field]

        # Check that no two fields share the same name.
        for field in self.fields:
            if field.name in self._fields_by_name:
                orig_lineno = self._fields_by_name[field.name]._token.lineno
                raise InvalidSpec("Field '%s' already defined on line %s." %
                                  (field.name, orig_lineno),
                                  field._token.lineno)
            self._fields_by_name[field.name] = field

        self.parent_type = parent_type
        if self.parent_type:
            if isinstance(parent_type, ForeignRef):
                self.parent_type_deref = self.parent_type.data_type
            else:
                self.parent_type_deref = self.parent_type
        else:
            self.parent_type_deref = None

        # Check that the fields for this type do not match any of the fields of
        # its parents.
        cur_type = self.parent_type_deref
        while cur_type:
            for field in self.fields:
                if field.name in cur_type._fields_by_name:
                    lineno = cur_type._fields_by_name[field.name]._token.lineno
                    raise InvalidSpec(
                        "Field '%s' already defined in parent '%s' on line %d."
                        % (field.name, cur_type.name, lineno),
                        field._token.lineno)
            cur_type = cur_type.parent_type_deref

        # Indicate that the attributes of the type have been populated.
        self._is_forward_ref = False

    @property
    def all_fields(self):
        raise NotImplementedError

    def has_documented_type_or_fields(self, include_inherited_fields=False):
        """Returns whether this type, or any of its fields, are documented.

        Use this when deciding whether to create a block of documentation for
        this type.
        """
        if self.doc:
            return True
        else:
            return self.has_documented_fields(include_inherited_fields)

    def has_documented_fields(self, include_inherited_fields=False):
        """Returns whether at least one field is documented."""
        fields = self.all_fields if include_inherited_fields else self.fields
        for field in fields:
            if field.doc:
                return True
        return False

    @property
    def name(self):
        return self._name

    def copy(self):
        return copy.deepcopy(self)

    def prepend_field(self, field):
        self.fields.insert(0, field)

    def get_examples(self):
        """Returns an OrderedDict mapping labels to Example objects."""
        # Copy it just in case the caller wants to mutate the object.
        return copy.deepcopy(self._examples)

class Example(object):
    """An example of a struct or union type."""

    def __init__(self, label, text, value, token=None):
        assert isinstance(label, six.text_type), type(label)
        self.label = label
        assert isinstance(text, (six.text_type, type(None))), type(text)
        self.text = text
        assert isinstance(value, (six.text_type, OrderedDict)), type(value)
        self.value = value
        self._token = token

    def __repr__(self):
        return 'Example({!r}, {!r}, {!r})'.format(
            self.label, self.text, self.value)

class Struct(CompositeType):
    """
    Defines a product type: Composed of other primitive and/or struct types.
    """

    composite_type = 'struct'

    def set_attributes(self, doc, fields, parent_type=None):
        """
        See :meth:`CompositeType.set_attributes` for parameter definitions.
        """

        if parent_type:
            assert (isinstance(parent_type, Struct) or
                    (isinstance(parent_type, ForeignRef) and
                     isinstance(parent_type.data_type, Struct)))

        self.subtypes = []

        # These are only set if this struct enumerates subtypes.
        self._enumerated_subtypes = None  # Optional[List[Tuple[str, DataType]]]
        self._is_catch_all = None  # Optional[Bool]

        super(Struct, self).set_attributes(doc, fields, parent_type)

        if self.parent_type_deref:
            self.parent_type_deref.subtypes.append(self)

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
        if self.parent_type:
            if isinstance(self.parent_type, ForeignRef):
                parent_type = self.parent_type.data_type
            else:
                parent_type = self.parent_type
            fields.extend(parent_type._filter_fields(filter_function))
        fields.extend(filter(filter_function, self.fields))
        return fields

    @property
    def all_required_fields(self):
        """
        Returns an iterator that traverses required fields in all super types
        first, and then for this type.
        """
        def required_check(f):
            return not is_nullable_type(f.data_type) and not f.has_default
        return self._filter_fields(required_check)

    @property
    def all_optional_fields(self):
        """
        Returns an iterator that traverses optional fields in all super types
        first, and then for this type.
        """
        def optional_check(f):
            return is_nullable_type(f.data_type) or f.has_default
        return self._filter_fields(optional_check)

    def has_enumerated_subtypes(self):
        """
        Whether this struct enumerates its subtypes.
        """
        return bool(self._enumerated_subtypes)

    def get_enumerated_subtypes(self):
        """
        Returns a list of subtype fields. Each field has a `name` attribute
        which is the tag for the subtype. Each field also has a `data_type`
        attribute that is a `Struct` object representing the subtype.
        """
        assert self._enumerated_subtypes is not None
        return self._enumerated_subtypes

    def is_member_of_enumerated_subtypes_tree(self):
        """
        Whether this struct enumerates subtypes or is a struct that is
        enumerated by its parent type. Because such structs are serialized
        and deserialized differently, use this method to detect these.
        """
        return (self.has_enumerated_subtypes() or
                (self.parent_type_deref and
                 self.parent_type_deref.has_enumerated_subtypes()))

    def is_catch_all(self):
        """
        Indicates whether this struct should be used in the event that none of
        its known enumerated subtypes match a received type tag.

        Use this method only if the struct has enumerated subtypes.

        Returns: bool
        """
        assert self._enumerated_subtypes is not None
        return self._is_catch_all

    def set_enumerated_subtypes(self, subtype_fields, is_catch_all):
        """
        Sets the list of "enumerated subtypes" for this struct. This differs
        from regular subtyping in that each subtype is associated with a tag
        that is used in the serialized format to indicate the subtype. Also,
        this list of subtypes was explicitly defined in an "inner-union" in the
        specification. The list of fields must include all defined subtypes of
        this struct.

        NOTE(kelkabany): For this to work with upcoming forward references, the
        hierarchy of parent types for this struct must have had this method
        called on them already.

        :type subtype_fields: List[UnionField]
        """
        assert self._enumerated_subtypes is None, \
            'Enumerated subtypes already set.'
        assert isinstance(is_catch_all, bool), type(is_catch_all)

        self._is_catch_all = is_catch_all
        self._enumerated_subtypes = []

        # Require that if this struct enumerates subtypes, its parent (and thus
        # the entire hierarchy above this struct) does as well.
        if self.parent_type and not self.parent_type.has_enumerated_subtypes():
            raise InvalidSpec(
                "'%s' cannot enumerate subtypes if parent '%s' does not." %
                (self.name, self.parent_type.name), self._token.lineno)

        enumerated_subtype_names = set()  # Set[str]
        for subtype_field in subtype_fields:
            lineno = subtype_field._token.lineno

            # Require that a subtype only has a single type tag.
            if subtype_field.data_type.name in enumerated_subtype_names:
                raise InvalidSpec(
                    "Subtype '%s' can only be specified once." %
                    subtype_field.data_type.name, lineno)

            # Require that a subtype has this struct as its parent.
            if subtype_field.data_type.parent_type != self:
                raise InvalidSpec(
                    "'%s' is not a subtype of '%s'." %
                    (subtype_field.data_type.name, self.name), lineno)

            # Check for subtype tags that conflict with this struct's
            # non-inherited fields.
            if subtype_field.name in self._fields_by_name:
                # Since the union definition comes first, use its line number
                # as the source of the field's original declaration.
                raise InvalidSpec(
                    "Field '%s' already defined on line %d." %
                    (subtype_field.name, lineno),
                    self._fields_by_name[subtype_field.name]._token.lineno)

            # Walk up parent tree hierarchy to ensure no field conflicts.
            # Checks for conflicts with subtype tags and regular fields.
            cur_type = self.parent_type
            while cur_type:
                if subtype_field.name in cur_type._fields_by_name:
                    orig_field = cur_type._fields_by_name[subtype_field.name]
                    raise InvalidSpec(
                        "Field '%s' already defined in parent '%s' on line %d."
                        % (subtype_field.name, cur_type.name,
                           orig_field._token.lineno),
                        lineno)
                cur_type = cur_type.parent_type

            # Note the discrepancy between `fields` which contains only the
            # struct fields, and `_fields_by_name` which contains the struct
            # fields and enumerated subtype fields.
            self._fields_by_name[subtype_field.name] = subtype_field
            enumerated_subtype_names.add(subtype_field.data_type.name)
            self._enumerated_subtypes.append(subtype_field)

        assert len(self._enumerated_subtypes) > 0

        # Check that all known subtypes are listed in the enumeration.
        for subtype in self.subtypes:
            if subtype.name not in enumerated_subtype_names:
                raise InvalidSpec(
                    "'%s' does not enumerate all subtypes, missing '%s'" %
                    (self.name, subtype.name),
                    self._token.lineno)

    def get_all_subtypes_with_tags(self):
        """
        Unlike other enumerated-subtypes-related functionality, this method
        returns not just direct subtypes, but all subtypes of this struct. The
        tag of each subtype is the tag of the enumerated subtype from which it
        descended, which means that it's likely that subtypes will share the
        same tag.

        This method only applies to structs that enumerate subtypes.

        Use this when you need to generate a lookup table for a root struct
        that maps a generated class representing a subtype to the tag it needs
        in the serialized format.

        Returns:
            List[Tuple[String, Struct]]
        """
        assert self.has_enumerated_subtypes(), 'Enumerated subtypes not set.'
        subtypes_with_tags = []  # List[Tuple[String, Struct]]
        for subtype_field in self.get_enumerated_subtypes():
            subtypes_with_tags.append(
                (subtype_field.name, subtype_field.data_type))
            for subtype in subtype_field.data_type.subtypes:
                subtypes_with_tags.append(
                    (subtype_field.name, subtype))
        return subtypes_with_tags

    def _add_example(self, example):
        """Adds a "raw example" for this type.

        This does basic sanity checking to ensure that the example is valid
        (required fields specified, no unknown fields, correct types, ...).

        The example is not available via :meth:`get_examples` until
        :meth:`_compute_examples` is called.

        Args:
            example (babelapi.babel.parser.BabelExample): An example of this
                type.
        """
        if self.has_enumerated_subtypes():
            self._add_example_enumerated_subtypes_helper(example)
        else:
            self._add_example_helper(example)

    def _add_example_enumerated_subtypes_helper(self, example):
        """Validates examples for structs with enumerated subtypes."""

        if len(example.fields) != 1:
            raise InvalidSpec(
                'Example for struct with enumerated subtypes must only '
                'specify one subtype tag.', example.lineno, example.path)

        # Extract the only tag in the example.
        example_field = list(example.fields.values())[0]
        tag = example_field.name
        val = example_field.value
        if not isinstance(val, BabelExampleRef):
            raise InvalidSpec(
                "Example of struct with enumerated subtypes must be a "
                "reference to a subtype's example.",
                example_field.lineno, example_field.path)

        for subtype_field in self.get_enumerated_subtypes():
            if subtype_field.name == tag:
                self._raw_examples[example.label] = Example(
                    tag,
                    example.text,
                    OrderedDict([(tag, (val, subtype_field.data_type))]),
                    example)
                return
        else:
            raise InvalidSpec(
                "Unknown subtype tag '%s' in example." % tag,
                example_field.lineno, example_field.path)

    def _add_example_helper(self, example):
        """Validates examples for structs without enumerated subtypes."""

        # Check for fields in the example that don't belong.
        for label, example_field in example.fields.items():
            if not any(label == f.name for f in self.all_fields):
                raise InvalidSpec(
                    "Example for '%s' has unknown field '%s'." %
                    (self.name, label),
                    example_field.lineno, example_field.path,
                )

        # This stores a modified version of the example from the spec.
        ex_value = OrderedDict()

        for field in self.all_fields:
            dt, nullable_dt = get_underlying_type(field.data_type)
            list_dt = False
            while is_list_type(dt):
                dt = dt.data_type
                list_dt = True
            if field.name in example.fields:
                example_field = example.fields[field.name]
                if nullable_dt and example_field.value is None:
                    ex_value[field.name] = None
                elif isinstance(dt, CompositeType):
                    if isinstance(example_field.value, BabelExampleRef):
                        # This is a value that refers to an example of the
                        # field's data type.
                        ex_value[field.name] = example_field.value
                    else:
                        raise InvalidSpec(
                            "Field '%s' must be set to an example label for "
                            "type '%s'." % (field.name, dt.name),
                            example_field.lineno, example_field.path)
                elif list_dt:
                    # TODO(kelkabany): We need examples for lists, which we
                    # cannot even parse right now.
                    raise InvalidSpec(
                        "Example for field '%s' is unsupported because it's a "
                        "list of primitives." % field.name,
                        example_field.lineno, example_field.path)
                else:
                    try:
                        dt.check(example_field.value)
                    except ValueError as e:
                        raise InvalidSpec(
                            "Bad example for field '%s': %s" %
                            (field.name, e.args[0]),
                            example_field.lineno, example_field.path)
                    else:
                        ex_value[field.name] = example_field.value
            elif field.has_default:
                ex_value[field.name] = field.default
            elif list_dt or nullable_dt:
                # These don't need examples.
                pass
            else:
                raise InvalidSpec(
                    "Missing field '%s' in example." % field.name,
                    example.lineno, example.path)

        composite_example = Example(
            example.label, example.text, ex_value, example)
        self._raw_examples[example.label] = composite_example

    def _has_example(self, label):
        """Whether this data type has an example with the given ``label``."""
        return label in self._raw_examples

    def _compute_examples(self):
        """
        Populates the ``_examples`` instance attribute by computing full
        examples for each label in ``_raw_examples``.

        The logic in this method is separate from :meth:`_add_example` because
        this method requires that every type have ``_raw_examples`` assigned
        for resolving example references.
        """
        for label in self._raw_examples:
            self._examples[label] = self._compute_example(label)

    def _compute_example(self, label):
        if self.has_enumerated_subtypes():
            return self._compute_example_enumerated_subtypes(label)
        else:
            return self._compute_example_flat_helper(label)

    def _compute_example_flat_helper(self, label):
        """
        From the "raw example," resolves references to examples of other data
        types to compute the final example.

        Returns an Example object. The `value` attribute contains a
        JSON-serializable representation of the example.
        """
        assert label in self._raw_examples, label

        example = self._raw_examples[label]

        # Do a deep copy of the example because we're going to mutate it.
        ex_val = OrderedDict()

        for field in self.all_fields:
            dt, _ = get_underlying_type(field.data_type)
            list_nesting_count = 0
            while is_list_type(dt):
                dt = dt.data_type
                list_nesting_count += 1
            if field.name in example.value:
                val = example.value[field.name]
                if val is None:
                    # Serialized format doesn't include fields with null.
                    pass
                elif is_tag_ref(val):
                    ex_val[field.name] = val.tag_name
                elif isinstance(val, BabelExampleRef):
                    # Embed references to other examples directly.
                    if not dt._has_example(val.label):
                        raise InvalidSpec(
                            "Reference to example for '%s' with label '%s' "
                            "does not exist." % (dt.name, val.label),
                            val.lineno, val.path)
                    v = dt._compute_example(val.label).value
                    while list_nesting_count > 0:
                        v = [v]
                        list_nesting_count -= 1
                    ex_val[field.name] = v
                else:
                    # Use value as is
                    ex_val[field.name] = val
            elif list_nesting_count > 0:
                # For lists of primitives, automatically set the example to
                # an empty list.
                v = []
                while list_nesting_count > 1:
                    v = [v]
                    list_nesting_count -= 1
                ex_val[field.name] = v

        return Example(example.label, example.text, ex_val)

    def _compute_example_enumerated_subtypes(self, label, root=True):
        """
        Analogous to :meth:`_compute_example_flat_helper` but for structs with
        enumerated subtypes.
        """
        assert label in self._raw_examples, label

        example = self._raw_examples[label]

        if self.has_enumerated_subtypes():
            tag, (ref, data_type) = list(example.value.items())[0]
            if not data_type._has_example(ref.label):
                raise InvalidSpec(
                    "Reference to example for '%s' with label '%s' does not "
                    "exist." % (data_type.name, ref.label),
                    ref.lineno, ref.path)
            flat_example, ex_sub_value = \
                data_type._compute_example_enumerated_subtypes(ref.label, False)
            ex_value = OrderedDict()
            ex_value[tag] = ex_sub_value
            for field in self.fields:
                if field.name in flat_example.value:
                    ex_value[field.name] = flat_example.value[field.name]
                    del flat_example.value[field.name]
            if root:
                return Example(label, example.text, ex_value)
            else:
                return flat_example, ex_value
        else:
            # If we're at a leaf of a subtypes tree, then compute the example
            # as if it were a flat struct. The caller is responsible for moving
            # fields into different nesting levels based on the subtypes tree.
            flat_example = self._compute_example_flat_helper(label)
            ex_value = OrderedDict()
            for field in self.fields:
                if field.name in flat_example.value:
                    ex_value[field.name] = flat_example.value[field.name]
                    del flat_example.value[field.name]
            return flat_example, ex_value

    def __repr__(self):
        return 'Struct(%r, %r)' % (self.name, self.fields)

class Union(CompositeType):
    """Defines a tagged union. Fields are variants."""

    composite_type = 'union'

    def set_attributes(self, doc, fields, parent_type=None, catch_all_field=None):
        """
        :param UnionField catch_all_field: The field designated as the
            catch-all. This field should be a member of the list of fields.

        See :meth:`CompositeType.set_attributes` for parameter definitions.
        """
        if parent_type:
            assert (isinstance(parent_type, Union) or
                    (isinstance(parent_type, ForeignRef) and
                     isinstance(parent_type.data_type, Union)))

        super(Union, self).set_attributes(doc, fields, parent_type)

        self.catch_all_field = catch_all_field
        self.parent_type = parent_type

    def check(self, val):
        if not isinstance(val, TagRef):
            raise ValueError('%r is not a tag of %s' % (val, self.name))
        for field in self.all_fields:
            if val.tag_name == field.name:
                if not is_void_type(field.data_type):
                    raise ValueError('invalid reference to non-void tag %r' %
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
        if self.parent_type:
            parent_dt, _ = get_underlying_type(self.parent_type)
            fields.extend(parent_dt.all_fields)
        fields.extend([f for f in self.fields])
        return fields

    def _add_example(self, example):
        """Adds a "raw example" for this type.

        This does basic sanity checking to ensure that the example is valid
        (required fields specified, no unknown fields, correct types, ...).

        The example is not available via :meth:`get_examples` until
        :meth:`_compute_examples` is called.

        Args:
            example (babelapi.babel.parser.BabelExample): An example of this
                type.
        """
        if len(example.fields) != 1:
            raise InvalidSpec(
                'Example for union must specify exactly one tag.',
                example.lineno, example.path)

        # Extract the only tag in the example.
        example_field = list(example.fields.values())[0]
        tag = example_field.name
        val = example_field.value

        # Find the union member that corresponds to the tag.
        for field in self.all_fields:
            if tag == field.name:
                break
        else:
            # Error: Tag doesn't match any union member.
            raise InvalidSpec(
                "Unknown tag '%s' in example." % tag,
                example.lineno, example.path
            )

        dt, nullable_dt = get_underlying_type(field.data_type)
        while is_list_type(dt):
            dt = dt.data_type
        if val is None:
            # null can only be explicit for a nullable or void type
            if not nullable_dt and not is_void_type(dt):
                raise InvalidSpec(
                    "Tag '%s' is not nullable but is set to null by example." %
                    tag, example_field.lineno, example_field.path)
            else:
                # Use the compact representation (just the tag, no value)
                composite_example = Example(
                    example.label, example.text, tag)
        elif isinstance(dt, CompositeType):
            if isinstance(val, BabelExampleRef):
                composite_example = Example(
                    example.label, example.text, OrderedDict([(tag, val)]))
            else:
                raise InvalidSpec(
                    "Example for field '%s' must be reference to example "
                    "for '%s'." % (field.name, dt.name),
                    example_field.lineno, example_field.path)
        else:
            try:
                dt.check(val)
            except ValueError as e:
                raise InvalidSpec(
                    "Tag '%s' had bad example: %s" % (field.name, e.args[0]),
                    example_field.lineno, example_field.path)
            else:
                composite_example = Example(
                    example.label, example.text, OrderedDict([(tag, val)]))

        self._raw_examples[example.label] = composite_example

    def _has_example(self, label):
        """Whether this data type has an example with the given ``label``."""
        if label in self._raw_examples:
            return True
        else:
            for field in self.all_fields:
                dt, _ = get_underlying_type(field.data_type)
                if not is_composite_type(dt) and not is_void_type(dt):
                    continue
                if label == field.name:
                    return True
            else:
                return False

    def _compute_examples(self):
        """
        Populates the ``_examples`` instance attribute by computing full
        examples for each label in ``_raw_examples``.

        The logic in this method is separate from :meth:`_add_example` because
        this method requires that every type have ``_raw_examples`` assigned
        for resolving example references.
        """
        for label in self._raw_examples:
            self._examples[label] = self._compute_example(label)

        # Add examples for each void union member.
        for field in self.all_fields:
            dt, _ = get_underlying_type(field.data_type)
            if is_void_type(dt):
                self._examples[field.name] = \
                    Example(field.name, None, field.name)

    def _compute_example(self, label):
        """
        From the "raw example," resolves references to examples of other data
        types to compute the final example.

        Returns an Example object. The `value` attribute contains a
        JSON-serializable representation of the example.
        """
        if label in self._raw_examples:
            example = self._raw_examples[label]

            # Do a deep copy of the example because we're going to mutate it.
            example_copy = copy.deepcopy(example)

            if isinstance(example.value, six.text_type):
                # If it's a compact representation, we can just return it.
                return Example(example.label, example.text, example.value)

            assert len(example.value) == 1  # Verified in _add_raw_example()
            tag, val = list(example.value.items())[0]
            # Find the field referenced by this tag.
            for field in self.all_fields:
                if tag == field.name:
                        break
            else:
                raise AssertionError('Unknown tag %r' % tag)

            dt, _ = get_underlying_type(field.data_type)
            list_nesting_count = 0
            while is_list_type(dt):
                dt = dt.data_type
                list_nesting_count += 1
            if isinstance(val, BabelExampleRef):
                # If it's a reference to an example, inject it in.
                if not dt._has_example(val.label):
                    raise InvalidSpec(
                        "Reference to example for '%s' with label '%s' does not "
                        "exist." % (dt.name, val.label), val.lineno, val.path)
                ex_val = dt._compute_example(val.label).value
            else:
                assert isinstance(dt, PrimitiveType), dt
                ex_val = val
            while list_nesting_count > 0:
                ex_val = [ex_val]
                list_nesting_count -= 1
            example_copy.value = {tag: ex_val}

            return example_copy

        else:
            # Try to fallback to a union member with tag matching the label
            # with a data type that is composite or void.
            for field in self.all_fields:
                if label == field.name:
                    break
            else:
                raise AssertionError('No example for label %r' % label)

            assert is_void_type(field.data_type)
            return Example(field.name, field.doc, field.name)

    def unique_field_data_types(self):
        """
        Checks if all variants have different data types.

        If so, the selected variant can be determined just by the data type of
        the value without needing a field name / tag. In some languages, this
        lets us make a shortcut
        """
        data_type_names = set()
        for field in self.fields:
            if not is_void_type(field.data_type):
                if field.data_type.name in data_type_names:
                    return False
                else:
                    data_type_names.add(field.data_type.name)
        else:
            return True

    def __repr__(self):
        return 'Union(%r, %r)' % (self.name, self.fields)

class ForeignRef(object):
    """
    Used when a reference is made to a type in a different namespace.
    """

    def __init__(self, namespace_name, data_type):
        """
        Args:
            namespace_name (str): The name of the namespace this data type
                belongs to.
            data_type (DataType): The referenced data type.
        """
        assert isinstance(data_type, DataType), type(data_type)
        self.namespace_name = namespace_name
        self.data_type = data_type

    @property
    def name(self):
        """Return the namespace name concatenated with the data type's name.

        This is a convenience so a set of composite and foreign data
        types can be sorted by the 'name' attribute.
        """
        return '{}.{}'.format(self.namespace_name, self.data_type.name)

    def __repr__(self):
        return 'ForeignRef(%r, %r)' % (self.namespace_name, self.data_type)

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

def get_underlying_type(data_type):
    """
    Convenience method to ignore ForeignRef and/or Nullable wrappers around
    a DataType.

    Args:
        data_type (DataType): The type to unwrap.

    Return:
        Tuples[DataType, bool]: The underlying data type and a bool indicating
            whether the input type was nullable.
    """
    if is_foreign_ref(data_type):
        dt = data_type.data_type
    else:
        dt = data_type
    if is_nullable_type(dt):
        return dt.data_type, True
    else:
        return dt, False

def is_binary_type(data_type):
    return isinstance(data_type, Binary)
def is_boolean_type(data_type):
    return isinstance(data_type, Boolean)
def is_composite_type(data_type):
    return isinstance(data_type, CompositeType)
def is_integer_type(data_type):
    return isinstance(data_type, (UInt32, UInt64, Int32, Int64))
def is_float_type(data_type):
    return isinstance(data_type, (Float32, Float64))
def is_foreign_ref(data_type):
    return isinstance(data_type, ForeignRef)
def is_list_type(data_type):
    return isinstance(data_type, List)
def is_nullable_type(data_type):
    return isinstance(data_type, Nullable)
def is_numeric_type(data_type):
    return is_integer_type(data_type) or is_float_type(data_type)
def is_primitive_type(data_type):
    return isinstance(data_type, PrimitiveType)
def is_string_type(data_type):
    return isinstance(data_type, String)
def is_struct_type(data_type):
    return isinstance(data_type, Struct)
def is_tag_ref(val):
    return isinstance(val, TagRef)
def is_timestamp_type(data_type):
    return isinstance(data_type, Timestamp)
def is_union_type(data_type):
    return isinstance(data_type, Union)
def is_void_type(data_type):
    return isinstance(data_type, Void)
