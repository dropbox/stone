import pprint

# language by language regex for finding what functions have already been defined

from babelsdk.lang.lang import TargetLanguage
from babelsdk.data_type import (
    Boolean,
    Float,
    Int32,
    Int64,
    List,
    String,
    Timestamp,
    UInt32,
    UInt64,
)

class RubyTargetLanguage(TargetLanguage):

    _language_short_name = 'rb'

    def get_supported_extensions(self):
        return ('.rb', )

    _type_table = {
        Boolean: 'boolean',
        Float: 'Float',
        Int32: 'Integer',
        Int64: 'Integer',
        List: 'Array',
        String: 'String',
        UInt32: 'Integer',
        UInt64: 'Integer',
        Timestamp: 'DateTime',
    }

    def format_type(self, data_type):
        return RubyTargetLanguage._type_table.get(data_type.__class__, data_type.name)

    def format_obj(self, o):
        assert not isinstance(o, dict), "Bad argument to format_obj: pprint's dict formatting is not valid Ruby."
        return pprint.pformat(o, width=1)

    def format_variable(self, words):
        return '_'.join([word.lower() for word in words])

    def format_class(self, words):
        return ''.join([word.capitalize() for word in words])

    def format_method(self, words):
        return '_'.join([word.lower() for word in words])
