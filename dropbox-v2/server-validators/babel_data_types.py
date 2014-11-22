"""
Basic data types that should be re-usable by all Python code generators.
"""

from abc import ABCMeta, abstractmethod
import numbers
import re
import types

class DataType(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, val):
        """Checks if val is a valid value for this type."""
        pass

class Boolean(DataType):
    def validate(self, val):
        if not isinstance(val, bool):
            raise ValueError('%r is not a valid boolean' % val)

class _Integer(DataType):
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
        return '%s()' % self.__name__

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

class String(DataType):
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

import datetime

class Timestamp(DataType):
    def __init__(self, format):
        assert isinstance(format, str), (
            'format must be a string'
        )
        self.format = format

    def validate(self, val):
        if not isinstance(val, datetime.datetime):
            raise ValueError('%r is of type %r and is not a valid timestamp'
                             % (val, type(val).__name__))
        """
        if isinstance(val, types.StringTypes):
            # Raises a ValueError if val is the incorrect format
            datetime.datetime.strptime(val, self.format)
        elif isinstance(val, datetime.datetime):
            pass
        else:
            raise ValueError('%r is of type %r and is not a valid string'
                             % (val, type(val).__name__))
        """

class List(DataType):
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

class Name(object):
    __familiar_name_data_type = String()

    def __init__(self):
        self._familiar_name = None
        self.__has_familiar_name = False

    def validate(self):
        if not self.__has_familiar_name:
            raise KeyError('missing familiar_name')

    @property
    def familiar_name(self):
        if self.__has_familiar_name:
            return self._familiar_name
        elif self.__familiar_name_optional:
            return self.__familiar_name_default
        else:
            raise KeyError('familiar_name has not been set')

    @familiar_name.setter
    def familiar_name(self, val):
        self.__familiar_name_data_type.validate(val)
        self._familiar_name = val
        self.__has_familiar_name = True

    @familiar_name.deleter
    def familiar_name(self):
        self._familiar_name = None
        self.__has_familiar_name = False

    @classmethod
    def from_json_serializable_dict(cls, obj):
        name = cls()
        if 'familiar_name' not in obj:
            raise KeyError('familiar_name missing')
        name.familiar_name = obj['familiar_name']
        return name

    def to_dict(self, transformer):
        return {
            'familiar_name': self._familiar_name,
        }

class DictTransformer(object):
    @staticmethod
    def convert_to(data_type, val):
        raise NotImplemented
    @staticmethod
    def convert_from(self):
        raise NotImplemented

class JsonCompatibleDictTransformer(DictTransformer):
    """
    Converts a Python dictionary to one that is compatible with
    JSON.
    """
    @staticmethod
    def convert_to(data_type, val):
        if val is None:
            return val
        elif isinstance(data_type, (Timestamp,)):
            return val.strftime(data_type.format)
        else:
            return val

    @staticmethod
    def convert_from(data_type, val):
        #print '1', data_type, val
        if val is None:
            #print '2', data_type, val
            return val
        elif isinstance(data_type, (Timestamp,)):
            #print '3', data_type, val
            return datetime.datetime.strptime(val, data_type.format)
        else:
            #print '4', data_type, val
            return val

class MeInfo(object):
    """
    This is a test
    :ivar account_id: The account!
    """

    __account_id_data_type = String()
    __account_id_optional = False
    __account_id_default = None

    def __init__(self):
        """Hello"""
        self._account_id = None
        self._name = None

        self.__has_account_id = False
        self.__has_name = False

    def validate(self):
        """Checks for missing fields."""
        if not self.__has_account_id:
            raise KeyError('missing account_id')
        if not self.__has_name:
            raise KeyError('missing name')
        else:
            self._name.validate()

    @property
    def account_id(self):
        if self.__has_account_id:
            return self._account_id
        elif self.__account_id_optional:
            return self.__account_id_default
        else:
            raise KeyError('account_id has not been set')

    @account_id.setter
    def account_id(self, val):
        self.__account_id_data_type.validate(val)
        self._account_id = val
        self.__has_account_id = True

    @account_id.deleter
    def account_id(self):
        self._account_id = None
        self.__has_account_id = False

    @property
    def name(self):
        """GET NAME"""
        if self.__has_name:
            return self._name
        else:
            raise KeyError('name has not been set')

    @name.setter
    def name(self, val):
        """SET NAME"""
        if isinstance(val, Name):
            # TODO: Do we want to validate here, or later?
            self._name = val
            self.__has_name = True
        else:
            raise TypeError('name is of type %r but must be of type Name'
                            % type(val).__name__)

    @classmethod
    def from_dict(cls, transformer, obj):
        # TODO: Blow up on extra fields
        me_info = cls()
        if 'account_id' not in obj:
            raise KeyError("'account_id' is missing")
        me_info.account_id = transformer.untransform(cls.__account_id_data_type, obj['account_id'])
        if 'name' not in obj:
            raise KeyError("'name' is missing")
        me_info.name = Name.from_dict(transformer, obj['name'])
        return me_info

    def to_dict(self, transformer):
        return {
            'account_id': transformer.transform(self.__account_id_data_type, self._account_id),
            'name': self._name.to_dict(transformer),
        }

me = MeInfo()
n = Name()

#me.validate()
import os

#print me.account_id
#print MeInfo.zero

MeInfo.account_id

print MeInfo.name


