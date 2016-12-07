from __future__ import absolute_import, division, print_function, unicode_literals

# Hack to get around some of Python 2's standard library modules that
# accept ascii-encodable unicode literals in lieu of strs, but where
# actually passing such literals results in errors with mypy --py2. See
# <https://github.com/python/typeshed/issues/756> and
# <https://github.com/python/mypy/issues/2536>.
import importlib
import typing  # noqa: F401 # pylint: disable=unused-import
argparse = importlib.import_module(str('argparse'))  # type: typing.Any

from stone.generator import CodeGenerator
from stone.target.js_helpers import (
    fmt_error_type,
    fmt_func,
    fmt_obj,
    fmt_type,
)

_cmdline_parser = argparse.ArgumentParser(prog='js-client-generator')
_cmdline_parser.add_argument(
    'filename',
    help=('The name to give the single Javascript file that is created and '
          'contains all of the routes.'),
)
_cmdline_parser.add_argument(
    '-c',
    '--class-name',
    type=str,
    help=('The name of the class the generated functions will be attached to. '
          'The name will be added to each function documentation, which makes '
          'it available for tools like JSDoc.'),
)

_header = """\
// Auto-generated by Stone, do not modify.
var routes = {};
"""


class JavascriptClientGenerator(CodeGenerator):
    """Generates a single Javascript file with all of the routes defined."""

    cmdline_parser = _cmdline_parser

    # Instance var of the current namespace being generated
    cur_namespace = None

    preserve_aliases = True

    def generate(self, api):
        with self.output_to_relative_path(self.args.filename):

            self.emit_raw(_header)

            for namespace in api.namespaces.values():
                for route in namespace.routes:
                    self._generate_route(
                        api.route_schema, namespace, route)

            self.emit()

            self.emit('module.exports = routes;')

    def _generate_route(self, route_schema, namespace, route):
        function_name = fmt_func(namespace.name + '_' + route.name)
        self.emit()
        self.emit('/**')
        if route.doc:
            self.emit_wrapped_text(self.process_doc(route.doc, self._docf), prefix=' * ')
        if self.args.class_name:
            self.emit(' * @function {}#{}'.format(self.args.class_name,
                                                  function_name))
        if route.deprecated:
            self.emit(' * @deprecated')

        self.emit(' * @arg {%s} arg - The request parameters.' %
                  fmt_type(route.arg_data_type))
        self.emit(' * @returns {Promise.<%s, %s>}' %
                (fmt_type(route.result_data_type),
                 fmt_error_type(route.error_data_type)))
        self.emit(' */')
        self.emit('routes.%s = function (arg) {' % function_name)
        with self.indent(dent=2):
            url = '{}/{}'.format(namespace.name, route.name)
            if route_schema.fields:
                additional_args = []
                for field in route_schema.fields:
                    additional_args.append(fmt_obj(route.attrs[field.name]))
                self.emit(
                    "return this.request('{}', arg, {});".format(
                        url, ', '.join(additional_args)))
            else:
                self.emit(
                    'return this.request("%s", arg);' % url)
        self.emit('};')

    def _docf(self, tag, val):  # pylint: disable=unused-argument
        """
        Callback used as the handler argument to process_docs(). This converts
        Stone doc references to JSDoc-friendly annotations.
        """
        # TODO(kelkabany): We're currently just dropping all doc ref tags.
        return val
