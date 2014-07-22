import copy
import pprint
import re

# language by language regex for finding what functions have already been defined

from babelsdk.lang.lang import TargetLanguage
from babelsdk.data_type import (
    Boolean,
    Float,
    Int32,
    Int64,
    String,
    UInt32,
    UInt64,
)

class PythonTargetLanguage(TargetLanguage):

    _language_short_name = 'py'

    def get_supported_extensions(self):
        return ('.py', )

    _type_table = {
        Boolean: 'bool',
        Float: 'float',
        Int32: 'int',
        UInt32: 'long',
        Int64: 'long',
        UInt64: 'long',
        String: 'str',
    }

    def format_type(self, data_type):
        return PythonTargetLanguage._type_table[data_type]

    def format_obj(self, o):
        return pprint.pformat(o, width=1)

    def format_class(self, s):
        # Might be separated by _ or -
        words = re.split('\W+|-_', s)
        return ''.join([word.capitalize() for word in words])

    def format_method(self, s):
        words = re.split('\W+|-_', s)
        return '_'.join([word.lower() for word in words])

