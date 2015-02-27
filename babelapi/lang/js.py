import json

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

class JavascriptTargetLanguage(TargetLanguage):

    _language_short_name = 'js'

    def get_supported_extensions(self):
        return ('.js', )

    _type_table = {
        Boolean: 'boolean',
        Float32: 'number',
        Float64: 'number',
        Int32: 'number',
        Int64: 'number',
        List: 'object',
        String: 'string',
        UInt32: 'number',
        UInt64: 'number',
        Timestamp: 'object',
    }

    def format_type(self, data_type):
        return JavascriptTargetLanguage._type_table.get(data_type.__class__, data_type.name)

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
        return self.format_variable(self.split_words(name))
