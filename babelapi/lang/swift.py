from __future__ import absolute_import, division, print_function, unicode_literals

import pprint

# This file defines *stylistic* choices for Swift
# (ie, that class names are UpperCamelCase and that variables are lowerCamelCase)

from babelapi.lang.lang import TargetLanguage

class SwiftTargetLanguage(TargetLanguage):

    _language_short_name = 'swift'

    _reserved_words = {
        'description'
    }

    def get_supported_extensions(self):
        return ('.swift', )

    def format_obj(self, o):
        assert not isinstance(o, dict), "Only use for base type literals"
        if o is True:
            return 'true'
        if o is False:
            return 'false'
        if o is None:
            return 'nil'
        return pprint.pformat(o, width=1)

    def _format_camelcase(self, name, lower_first=True):
        words = [word.capitalize() for word in self.split_words(name)]
        if lower_first:
            words[0] = words[0].lower()
        ret = ''.join(words)
        if ret in self._reserved_words:
            ret += '_'
        return ret

    def format_variable(self, name):
        return self._format_camelcase(name)

    def format_class(self, name):
        return self._format_camelcase(name, lower_first=False)

    def format_method(self, name):
        return self._format_camelcase(name)
