from __future__ import absolute_import, division, print_function, unicode_literals

import pprint

from .helpers import split_words

# This file defines *stylistic* choices for Swift
# (ie, that class names are UpperCamelCase and that variables are lowerCamelCase)


_reserved_words = {
    'description'
}


def fmt_obj(o):
    assert not isinstance(o, dict), "Only use for base type literals"
    if o is True:
        return 'true'
    if o is False:
        return 'false'
    if o is None:
        return 'nil'
    return pprint.pformat(o, width=1)


def _format_camelcase(name, lower_first=True):
    words = [word.capitalize() for word in split_words(name)]
    if lower_first:
        words[0] = words[0].lower()
    ret = ''.join(words)
    if ret in _reserved_words:
        ret += '_'
    return ret


def fmt_class(name):
    return _format_camelcase(name, lower_first=False)


def fmt_func(name):
    return _format_camelcase(name)


def fmt_var(name):
    return _format_camelcase(name)

