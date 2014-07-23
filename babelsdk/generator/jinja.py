import copy
import json

import jinja2

from babelsdk.data_type import (
    Binary,
    List,
    Struct,
    Union,
)

from generator import Generator

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
        self.languages = [PythonTargetLanguage()]
        for language in self.languages:
            for ext in language.get_supported_extensions():
                self.ext_to_language[ext] = language

        self.env_vars = {'api': api}
        self.template_env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)

        # Default filter: Pretty JSON
        self.template_env.filters['pjson'] = lambda s: json.dumps(s, indent=2)
        self.template_env.filters['is_binary'] = lambda s: isinstance(s, Binary)
        self.template_env.filters['is_list'] = lambda s: isinstance(s, List)
        self.template_env.filters['is_struct'] = lambda s: isinstance(s, Struct)
        self.template_env.filters['is_union'] = lambda s: isinstance(s, Union)
        self.template_env.filters['is_composite'] = lambda s: isinstance(s, Union)

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
    def get_template_filters(language):
        return {'method': language.format_method,
                'class': language.format_class,
                'type': language.format_type,
                'pprint': language.format_obj,}
