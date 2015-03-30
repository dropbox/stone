from __future__ import absolute_import, division, print_function, unicode_literals

import pprint

# language by language regex for finding what functions have already been defined

from babelapi.lang.lang import TargetLanguage
from babelapi.data_type import (
    Boolean,
    Float32,
    Float64,
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
        Float32: 'Float',
        Float64: 'Float',
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
        assert not isinstance(o, dict), \
            "Bad argument to format_obj: pprint's dict formatting is not valid Ruby."
        if o is True:
            return 'true'
        if o is False:
            return 'false'
        return pprint.pformat(o, width=1)

    def format_variable(self, name):
        return '_'.join([word.lower() for word in self.split_words(name)])

    def format_class(self, name):
        return ''.join([word.capitalize() for word in self.split_words(name)])

    def format_method(self, name):
        return '_'.join([word.lower() for word in self.split_words(name)])
