import json
import pprint

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

class JavascriptTargetLanguage(TargetLanguage):

    _language_short_name = 'js'

    def get_supported_extensions(self):
        return ('.js', )

    _type_table = {
        Boolean: 'boolean',
        Float: 'number',
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

    def format_variable(self, words):
        for i, word in enumerate(words):
            if i == 0:
                words[i] = words[i].lower()
            else:
                words[i] = words[i].capitalize()
        return ''.join(words)

    def format_class(self, words):
        return ''.join([word.capitalize() for word in words])

    def format_method(self, words):
        return self.format_variable(words)
