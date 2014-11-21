import numbers
import re
import types

class Boolean(object):
    def validate(self, val):
        if not isinstance(val, bool):
            raise ValueError('%r is not a valid boolean' % val)

class _BoundedInteger(object):
    """
    When extending, specify 'minimum' and 'maximum' as class variables.
    """
    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            if min_value >= self.minimum:
                self.minimum = min_value
            else:
                raise ValueError('min_value cannot be less than the minimum '
                                 'value for this type (%s < %s)'
                                 % (min_value, self.minimum))
        if max_value is not None:
            if max_value <= self.maximum:
                self.maximum = max_value
            else:
                raise ValueError('max_value cannot be greater than the maximum '
                                 'value for this type (%s < %s)'
                                 % (max_value, self.maximum))

    def validate(self, val):
        if not isinstance(val, numbers.Integral):
            raise ValueError('%r is of type %r and is not a valid integer type'
                             % (val, type(val)))
        elif not (self.minimum <= val <= self.maximum):
            raise ValueError('%s is not within range [%r, %r]'
                             % (val, self.minimum, self.maximum))

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

class String(object):
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

class Timestamp(object):
    pass

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
        if isinstance(data_type, (Timestamp,)):
            return str(val)
        else:
            return val

    @staticmethod
    def convert_from(data_type, val):
        if isinstance(data_type, (Timestamp,)):
            import datetime
            return datetime.datetime.utcnow()
        else:
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


