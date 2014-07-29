import copy
import json

import jinja2
from jinja2.ext import Extension

from babelsdk.data_type import (
    Binary,
    List,
    Struct,
    Union,
)

from generator import Generator

import re

class Jinja2Generator(Generator):
    """
    Jinja2 templates will have access to the :class:`babelsdk.api.Api` object,
    as well as the following additional filters:

        pjson (pretty json), is_binary, is_list, is_struct, is_union, and
        is_composite.
    """

    def __init__(self, api):

        super(Jinja2Generator, self).__init__(api)

        # File extension -> Language
        self.ext_to_language = {}

        # Language -> dict of template filters
        self.language_to_template_filters = {}

        from babelsdk.lang.python import PythonTargetLanguage
        from babelsdk.lang.ruby import RubyTargetLanguage
        self.languages = [PythonTargetLanguage(), RubyTargetLanguage()]
        for language in self.languages:
            for ext in language.get_supported_extensions():
                self.ext_to_language[ext] = language

        self.env_vars = {'api': api}
        self.template_env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, extensions=[TrimExtension])

        # Default filter: Pretty JSON
        self.template_env.filters['pjson'] = lambda s: json.dumps(s, indent=2)
        self.template_env.filters['is_binary'] = lambda s: isinstance(s, Binary)
        self.template_env.filters['is_list'] = lambda s: isinstance(s, List)
        self.template_env.filters['is_struct'] = lambda s: isinstance(s, Struct)
        self.template_env.filters['is_union'] = lambda s: isinstance(s, Union)
        self.template_env.filters['is_composite'] = lambda s: isinstance(s, Union)

        # Filters for making it easier to render code (as opposed to HTML)

        # Jinja has format(pattern, text), but no way to do the reverse. This allows
        # us to take a string and insert it into a format string. For example,
        # Ruby symbols: {{ variable|inverse_format(':%s') }}
        self.template_env.filters['inverse_format'] = lambda text, pattern: pattern.format(text)

        # Simple wrapper for slicing a string
        # {{ str|string_slice(1,5,2) }} => str[1:5:2]
        self.template_env.filters['string_slice'] = self._string_slice

        # Add language specified filters
        for language in self.languages:
            for filter_name, method in self.get_template_filters(language).items():
                lang_filter_name = language.get_language_short_name() + filter_name
                self.template_env.filters[lang_filter_name] = method

        for language in self.languages:
            language_filters = copy.copy(self.template_env.filters)
            for filter_name, method in self.get_template_filters(language).items():
                language_filters[filter_name] = method
            self.language_to_template_filters[language] = language_filters


    def render(self, extension, text):
        if extension in self.ext_to_language:
            language = self.ext_to_language[extension]
            backup_filters = self.template_env.filters
            self.template_env.filters = self.language_to_template_filters[language]
            t = self.template_env.from_string(text)
            rendered_contents = t.render(self.env_vars)
            self.template_env.filters = backup_filters
        else:
            # for extensions like html...
            t = self.template_env.from_string(text)
            rendered_contents = t.render(self.env_vars)

        return rendered_contents

    @staticmethod
    def _string_slice(str, start=0, end=None, step=1):
        if end is None:
            end = len(str)
        return str[start:end:step]

    @staticmethod
    def get_template_filters(language):
        return {'method': lambda s: language.format_method(split_words(s)),
                'class': lambda s: language.format_class(split_words(s)),
                'type': language.format_type,
                'pprint': language.format_obj,}

def split_words(words):
    """
    Splits a word based on capitalization, dashes, or underscores.
        Example: 'GetFile' -> ['Get', 'File']
    """
    all_words = []
    for word in re.split('[\W|-|_]+', words):
        vals = re.findall('^[a-z0-9]+|[A-Z][a-z0-9]+|[A-Z]+(?=[A-Z][a-z0-9])|[A-Z]+$', word)
        if vals:
            all_words.extend(vals)
        else:
            all_words.append(word)
    return all_words


class TrimExtension(Extension):
    """
    A no-op tag for Jinja templates for whitespace control.

    This lets us control whitespace to keep template lines short. For example,
    to put many variables onto one line, we can use

    {{ one }}{%- trim -%}
    {{ two }}{%- trim -%}
    {{ three }}...

    instead of

    {{ one }}{{ two }}{{ three }}...
    """

    tags = set(['trim'])

    def parse(self, parser):
        parser.parse_expression()
        return []

