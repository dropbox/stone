from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

# Hack to get around some of Python 2's standard library modules that
# accept ascii-encodable unicode literals in lieu of strs, but where
# actually passing such literals results in errors with mypy --py2. See
# <https://github.com/python/typeshed/issues/756> and
# <https://github.com/python/mypy/issues/2536>.
import importlib
argparse = importlib.import_module(str('argparse'))  # type: typing.Any

from stone.backend import CodeBackend
from stone.backends.tsd_helpers import (
    check_route_name_conflict,
    fmt_error_type,
    fmt_func,
    fmt_tag,
    fmt_type,
)
from stone.ir import Void


_cmdline_parser = argparse.ArgumentParser(prog='tsd-client-backend')
_cmdline_parser.add_argument(
    'template',
    help=('A template to use when generating the TypeScript definition file.')
)
_cmdline_parser.add_argument(
    'filename',
    help=('The name to give the single TypeScript definition file to contain '
          'all of the emitted types.'),
)
_cmdline_parser.add_argument(
    '-t',
    '--template-string',
    type=str,
    default='ROUTES',
    help=('The name of the template string to replace with route definitions. '
          'Defaults to ROUTES, which replaces the string /*ROUTES*/ with route '
          'definitions.')
)
_cmdline_parser.add_argument(
    '-i',
    '--indent-level',
    type=int,
    default=1,
    help=('Indentation level to emit types at. Routes are automatically '
          'indented one level further than this.')
)
_cmdline_parser.add_argument(
    '-s',
    '--spaces-per-indent',
    type=int,
    default=2,
    help=('Number of spaces to use per indentation level.')
)
_cmdline_parser.add_argument(
    '--wrap-response-in',
    type=str,
    default='',
    help=('Wraps the response in a response class')
)

_header = """\
// Auto-generated by Stone, do not modify.
"""

class TSDClientBackend(CodeBackend):
    """Generates a TypeScript definition file with routes defined."""

    cmdline_parser = _cmdline_parser

    preserve_aliases = True

    def generate(self, api):
        spaces_per_indent = self.args.spaces_per_indent
        indent_level = self.args.indent_level
        template_path = os.path.join(self.target_folder_path, self.args.template)
        template_string = self.args.template_string

        with self.output_to_relative_path(self.args.filename):
            if os.path.isfile(template_path):
                with open(template_path, 'r') as template_file:
                    template = template_file.read()
            else:
                raise AssertionError('TypeScript template file does not exist.')

            # /*ROUTES*/
            r_match = re.search("/\\*%s\\*/" % (template_string), template)
            if not r_match:
                raise AssertionError(
                    'Missing /*%s*/ in TypeScript template file.' % template_string)

            r_start = r_match.start()
            r_end = r_match.end()
            r_ends_with_newline = template[r_end - 1] == '\n'
            t_end = len(template)
            t_ends_with_newline = template[t_end - 1] == '\n'

            self.emit_raw(template[0:r_start] + ('\n' if not r_ends_with_newline else ''))
            self._generate_routes(api, spaces_per_indent, indent_level)
            self.emit_raw(template[r_end + 1:t_end] + ('\n' if not t_ends_with_newline else ''))

    def _generate_routes(self, api, spaces_per_indent, indent_level):
        with self.indent(dent=spaces_per_indent * (indent_level + 1)):
            for namespace in api.namespaces.values():
                # first check for route name conflict
                check_route_name_conflict(namespace)
                for route in namespace.routes:
                    self._generate_route(
                        namespace, route)

    def _generate_route(self, namespace, route):
        function_name = fmt_func(namespace.name + '_' + route.name, route.version)
        self.emit()
        self.emit('/**')
        if route.doc:
            self.emit_wrapped_text(self.process_doc(route.doc, self._docf), prefix=' * ')
            self.emit(' *')
        self.emit_wrapped_text('When an error occurs, the route rejects the promise with type %s.'
                               % fmt_error_type(route.error_data_type), prefix=' * ')
        if route.deprecated:
            self.emit(' * @deprecated')

        if route.arg_data_type.__class__ != Void:
            self.emit(' * @param arg The request parameters.')
        self.emit(' */')

        return_type = None
        if self.args.wrap_response_in:
            if route.result_data_type.__class__ != Void:
                return_type = 'Promise<%s<%s>>;' %  (self.args.wrap_response_in, fmt_type(route.result_data_type))
            else:
                return_type = 'Promise<%s>;' % (fmt_type(route.result_data_type))
        else:
            return_type = 'Promise<%s>;' % (fmt_type(route.result_data_type))

        arg = ''
        if route.arg_data_type.__class__ != Void:
            arg = 'arg: %s' % fmt_type(route.arg_data_type)

        self.emit('public %s(%s): %s' % (function_name, arg, return_type))

    def _docf(self, tag, val):
        """
        Callback to process documentation references.
        """
        return fmt_tag(None, tag, val)
