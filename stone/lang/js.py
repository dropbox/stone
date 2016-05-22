from __future__ import absolute_import, division, print_function, unicode_literals

import json

from stone.lang.lang import TargetLanguage
from stone.data_type import (
    Boolean,
    Bytes,
    Float32,
    Float64,
    Int32,
    Int64,
    List,
    String,
    Timestamp,
    UInt32,
    UInt64,
    Void,
)

class JavascriptTargetLanguage(TargetLanguage):

    _language_short_name = 'js'

    def get_supported_extensions(self):
        return ('.js', )

    _type_table = {
        Boolean: 'Boolean',
        Bytes: 'String',
        Float32: 'Number',
        Float64: 'Number',
        Int32: 'Number',
        Int64: 'Number',
        List: 'Array',
        String: 'String',
        UInt32: 'Number',
        UInt64: 'Number',
        Timestamp: 'Object',
        Void: 'null',
    }

    def format_type(self, data_type):
        return JavascriptTargetLanguage._type_table.get(
            data_type.__class__, 'Object')

    def format_obj(self, o):
        return json.dumps(o, indent=2)

    def format_variable(self, name):
        words = self.split_words(name)
        for i, word in enumerate(words):
            if i == 0:
                words[i] = words[i].lower()
            else:
                words[i] = words[i].capitalize()
        return ''.join(words)

    def format_class(self, name):
        return ''.join([word.capitalize() for word in self.split_words(name)])

    def format_method(self, name):
        return self.format_variable(name)
