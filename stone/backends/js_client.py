from __future__ import absolute_import, division, print_function, unicode_literals

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression
    from stone.ir import ApiNamespace

# Hack to get around some of Python 2's standard library modules that
# accept ascii-encodable unicode literals in lieu of strs, but where
# actually passing such literals results in errors with mypy --py2. See
# <https://github.com/python/typeshed/issues/756> and
# <https://github.com/python/mypy/issues/2536>.
import importlib
argparse = importlib.import_module(str('argparse'))  # type: typing.Any

from stone.backend import CodeBackend
from stone.backends.js_helpers import (
    check_route_name_conflict,
    fmt_error_type,
    fmt_func,
    fmt_obj,
    fmt_type,
    fmt_url,
)
from stone.ir import Void

_cmdline_parser = argparse.ArgumentParser(prog='js-client-backend')
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
_cmdline_parser.add_argument(
    '--wrap-response-in',
    type=str,
    default='',
    help=('Wraps the response in a response class')
)

_header = """\
// Auto-generated by Stone, do not modify.
var routes = {};
"""


class JavascriptClientBackend(CodeBackend):
    """Generates a single Javascript file with all of the routes defined."""

    cmdline_parser = _cmdline_parser

    # Instance var of the current namespace being generated
    cur_namespace = None  # type: typing.Optional[ApiNamespace]

    preserve_aliases = True

    def generate(self, api):
        # first check for route name conflict
        with self.output_to_relative_path(self.args.filename):
            self.emit_raw(_header)
            for namespace in api.namespaces.values():
                # Hack: needed for _docf()
                self.cur_namespace = namespace

                check_route_name_conflict(namespace)
                for route in namespace.routes:
                    self._generate_route(api.route_schema, namespace, route)
            self.emit()
            self.emit('export { routes };')

    def _generate_route(self, route_schema, namespace, route):
        function_name = fmt_func(namespace.name + '_' + route.name, route.version)
        self.emit()
        self.emit('/**')
        if route.doc:
            self.emit_wrapped_text(self.process_doc(route.doc, self._docf), prefix=' * ')
        if self.args.class_name:
            self.emit(' * @function {}#{}'.format(self.args.class_name,
                                                  function_name))
        if route.deprecated:
            self.emit(' * @deprecated')

        return_type = None
        if self.args.wrap_response_in:
            if route.result_data_type.__class__ != Void:
                return_type = '%s<%s>' % (self.args.wrap_response_in,
                    fmt_type(route.result_data_type))
            else:
                return_type = fmt_type(route.result_data_type)
        else:
            return_type = fmt_type(route.result_data_type)

        if route.arg_data_type.__class__ != Void:
            self.emit(' * @arg {%s} arg - The request parameters.' %
                    fmt_type(route.arg_data_type))
        self.emit(' * @returns {Promise.<%s, %s>}' %
                (return_type,
                 fmt_error_type(route.error_data_type)))
        self.emit(' */')

        if route.arg_data_type.__class__ != Void:
            self.emit('routes.%s = function (arg) {' % (function_name))
        else:
            self.emit('routes.%s = function () {' % (function_name))
        with self.indent(dent=2):
            url = fmt_url(namespace.name, route.name, route.version)
            if route_schema.fields:
                additional_args = []
                for field in route_schema.fields:
                    additional_args.append(fmt_obj(route.attrs[field.name]))
                if route.arg_data_type.__class__ != Void:
                    self.emit(
                        "return this.request('{}', arg, {});".format(
                            url, ', '.join(additional_args)))
                else:
                    self.emit(
                        "return this.request('{}', null, {});".format(
                            url, ', '.join(additional_args)))
            else:
                if route.arg_data_type.__class__ != Void:
                    self.emit(
                        'return this.request("%s", arg);' % url)
                else:
                    self.emit(
                        'return this.request("%s", null);' % url)
        self.emit('};')

    def _docf(self, tag, val):
        """
        Callback used as the handler argument to process_docs(). This converts
        Stone doc references to JSDoc-friendly annotations.
        """
        # TODO(kelkabany): We're currently just dropping all doc ref tags ...
        # NOTE(praneshp): ... except for versioned routes
        if tag == 'route':
            if ':' in val:
                val, version = val.split(':', 1)
                version = int(version)
            else:
                version = 1
            url = fmt_url(self.cur_namespace.name, val, version)
            # NOTE: In js, for comments, we drop the namespace name and the '/' when
            # documenting URLs
            return url[(len(self.cur_namespace.name) + 1):]

        return val
