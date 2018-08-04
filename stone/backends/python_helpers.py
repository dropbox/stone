from __future__ import absolute_import, division, print_function, unicode_literals

from contextlib import contextmanager

import pprint

from stone.backend import Backend, CodeBackend  # noqa: F401 # pylint: disable=unused-import
from stone.backends.helpers import (
    fmt_pascal,
    fmt_underscores,
)
from stone.ir import ApiNamespace  # noqa: F401 # pylint: disable=unused-import
from stone.ir import (
    AnnotationType,
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
    is_user_defined_type,
    is_alias,
)

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

_type_table = {
    Boolean: 'bool',
    Bytes: 'bytes',
    Float32: 'float',
    Float64: 'float',
    Int32: 'int',
    Int64: 'long',
    List: 'list',
    String: 'str',
    Timestamp: 'datetime',
    UInt32: 'long',
    UInt64: 'long',
}

_reserved_keywords = {
    'break',
    'class',
    'continue',
    'for',
    'pass',
    'while',
    'async',
}

@contextmanager
def emit_pass_if_nothing_emitted(codegen):
    # type: (CodeBackend) -> typing.Iterator[None]
    starting_lineno = codegen.lineno
    yield
    ending_lineno = codegen.lineno
    if starting_lineno == ending_lineno:
        codegen.emit("pass")
        codegen.emit()

def _rename_if_reserved(s):
    if s in _reserved_keywords:
        return s + '_'
    else:
        return s

def fmt_class(name, check_reserved=False):
    s = fmt_pascal(name)
    return _rename_if_reserved(s) if check_reserved else s

def fmt_func(name, check_reserved=False, version=1):
    name = fmt_underscores(name)
    if check_reserved:
        name = _rename_if_reserved(name)
    if version > 1:
        name = '{}_v{}'.format(name, version)
    return name

def fmt_obj(o):
    return pprint.pformat(o, width=1)

def fmt_type(data_type):
    return _type_table.get(data_type.__class__, fmt_class(data_type.name))

def fmt_var(name, check_reserved=False):
    s = fmt_underscores(name)
    return _rename_if_reserved(s) if check_reserved else s

def fmt_namespace(name):
    return _rename_if_reserved(name)

def check_route_name_conflict(namespace):
    """
    Check name conflicts among generated route definitions. Raise a runtime exception when a
    conflict is encountered.
    """

    route_by_name = {}
    for route in namespace.routes:
        route_name = fmt_func(route.name, version=route.version)
        if route_name in route_by_name:
            other_route = route_by_name[route_name]
            raise RuntimeError(
                'There is a name conflict between {!r} and {!r}'.format(other_route, route))
        route_by_name[route_name] = route

TYPE_IGNORE_COMMENT = "  # type: ignore"

def generate_imports_for_referenced_namespaces(
        backend, namespace, insert_type_ignore=False):
    # type: (Backend, ApiNamespace, bool) -> None
    """
    Both the true Python backend and the Python PEP 484 Type Stub backend have
    to perform the same imports.

    :param insert_type_ignore: add a MyPy type-ignore comment to the imports in
        the except: clause.
    """

    imported_namespaces = namespace.get_imported_namespaces()
    if not imported_namespaces:
        return

    type_ignore_comment = TYPE_IGNORE_COMMENT if insert_type_ignore else ""

    backend.emit('try:')
    with backend.indent():
        backend.emit('from . import (')
        with backend.indent():
            for ns in imported_namespaces:
                backend.emit(fmt_namespace(ns.name) + ',')
        backend.emit(')')
    backend.emit('except (ImportError, SystemError, ValueError):')
    # Fallback if imported from outside a package.
    with backend.indent():
        for ns in imported_namespaces:
            backend.emit('import {namespace_name}{type_ignore_comment}'.format(
                namespace_name=fmt_namespace(ns.name),
                type_ignore_comment=type_ignore_comment
            ))
    backend.emit()

def generate_module_header(backend):
    backend.emit('# -*- coding: utf-8 -*-')
    backend.emit('# Auto-generated by Stone, do not modify.')
    # Silly way to not type ATgenerated in our code to avoid having this
    # file marked as auto-generated by our code review tool.
    backend.emit('# @{}'.format('generated'))
    backend.emit('# flake8: noqa')
    backend.emit('# pylint: skip-file')

# This will be at the top of every generated file.
_validators_import_template = """\
try:
    from . import stone_validators as bv
    from . import stone_base as bb
except (ImportError, SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import stone_validators as bv{type_ignore_comment}
    import stone_base as bb{type_ignore_comment}

"""
validators_import = _validators_import_template.format(type_ignore_comment="")
validators_import_with_type_ignore = _validators_import_template.format(
    type_ignore_comment=TYPE_IGNORE_COMMENT
)

def class_name_for_data_type(data_type, ns=None):
    """
    Returns the name of the Python class that maps to a user-defined type.
    The name is identical to the name in the spec.

    If ``ns`` is set to a Namespace and the namespace of `data_type` does
    not match, then a namespace prefix is added to the returned name.
    For example, ``foreign_ns.TypeName``.
    """
    assert is_user_defined_type(data_type) or is_alias(data_type), \
        'Expected composite type, got %r' % type(data_type)
    name = fmt_class(data_type.name)
    if ns and data_type.namespace != ns:
        # If from an imported namespace, add a namespace prefix.
        name = '{}.{}'.format(fmt_namespace(data_type.namespace.name), name)
    return name

def class_name_for_annotation_type(annotation_type, ns=None):
    """
    Same as class_name_for_data_type, but works with annotation types.
    """
    assert isinstance(annotation_type, AnnotationType)
    name = fmt_class(annotation_type.name)
    if ns and annotation_type.namespace != ns:
        # If from an imported namespace, add a namespace prefix.
        name = '{}.{}'.format(fmt_namespace(annotation_type.namespace.name), name)
    return name
