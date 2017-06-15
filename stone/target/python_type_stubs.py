from __future__ import absolute_import, division, print_function, unicode_literals

import textwrap
from contextlib import contextmanager

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

from stone.api import (  # noqa: F401 # pylint: disable=unused-import
    Api,
    ApiNamespace,
)
from stone.data_type import (  # noqa: F401 # pylint: disable=unused-import
    Alias,
    DataType,
    List,
    Map,
    Nullable,
    Struct,
    Timestamp,
    Union,
    is_union_type,
    is_user_defined_type,
    is_void_type,
    unwrap_aliases,
)
from stone.generator import CodeGenerator
from stone.target.python_helpers import (
    class_name_for_data_type,
    fmt_func,
    fmt_var,
    generate_imports_for_referenced_namespaces,
    validators_import_with_type_ignore,
)
from stone.target.python_type_mapping import (  # noqa: F401 # pylint: disable=unused-import
    OverrideDefaultTypesDict,
    map_stone_type_to_python_type,
)

@contextmanager
def emit_pass_if_nothing_emitted(codegen):
    # type: (CodeGenerator) -> typing.Iterator[None]
    starting_lineno = codegen.lineno
    yield
    ending_lineno = codegen.lineno
    if starting_lineno == ending_lineno:
        codegen.emit("pass")

class ImportTracker(object):
    def __init__(self):
        # type: () -> None
        self.cur_namespace_typing_imports = set()  # type: typing.Set[typing.Text]
        self.cur_namespace_adhoc_imports = set()  # type: typing.Set[typing.Text]

    def clear(self):
        # type: () -> None
        self.cur_namespace_typing_imports.clear()
        self.cur_namespace_adhoc_imports.clear()

    def _register_typing_import(self, s):
        # type: (typing.Text) -> None
        """
        Denotes that we need to import something specifically from the `typing` module.

        For example, _register_typing_import("Optional")
        """
        self.cur_namespace_typing_imports.add(s)

    def _register_adhoc_import(self, s):
        # type: (typing.Text) -> None
        """
        Denotes an ad-hoc import.

        For example,
        _register_adhoc_import("import datetime")
        or
        _register_adhoc_import("from xyz import abc")
        """
        self.cur_namespace_adhoc_imports.add(s)


class PythonTypeStubsGenerator(CodeGenerator):
    """Generates Python modules to represent the input Stone spec."""

    # Instance var of the current namespace being generated
    cur_namespace = None
    preserve_aliases = True
    import_tracker = ImportTracker()

    def __init__(self, *args, **kwargs):
        # type: (...) -> None
        super(PythonTypeStubsGenerator, self).__init__(*args, **kwargs)
        self._pep_484_type_mapping_callbacks = self._get_pep_484_type_mapping_callbacks()

    def generate(self, api):
        # type: (Api) -> None
        """
        Generates a module for each namespace.

        Each namespace will have Python classes to represent data types and
        routes in the Stone spec.
        """
        for namespace in api.namespaces.values():
            with self.output_to_relative_path('{}.pyi'.format(namespace.name)):
                self._generate_base_namespace_module(namespace)

    def _generate_base_namespace_module(self, namespace):
        # type: (ApiNamespace) -> None
        """Creates a module for the namespace. All data types and routes are
        represented as Python classes."""

        self.cur_namespace = namespace
        self.import_tracker.clear()
        self.emit('# -*- coding: utf-8 -*-')
        self.emit('# Auto-generated by Stone, do not modify.')
        self.emit('# flake8: noqa')
        self.emit('# pylint: skip-file')

        self.emit_raw(validators_import_with_type_ignore)

        # Generate import statements for all referenced namespaces.
        self._generate_imports_for_referenced_namespaces(namespace)

        for data_type in namespace.linearize_data_types():
            if isinstance(data_type, Struct):
                self._generate_struct_class(namespace, data_type)
            elif isinstance(data_type, Union):
                self._generate_union_class(namespace, data_type)
            else:
                raise TypeError('Cannot handle type %r' % type(data_type))

        for alias in namespace.linearize_aliases():
            self._generate_alias_definition(namespace, alias)

        self._generate_imports_needed_for_typing()

    def _generate_imports_for_referenced_namespaces(self, namespace):
        # type: (ApiNamespace) -> None
        generate_imports_for_referenced_namespaces(
            generator=self,
            namespace=namespace,
            insert_type_ignore=True
        )

    def _generate_struct_class(self, ns, data_type):
        # type: (ApiNamespace, Struct) -> None
        """Defines a Python class that represents a struct in Stone."""
        self.emit(self._class_declaration_for_type(ns, data_type))
        with self.indent():
            self._generate_struct_class_init(ns, data_type)
            self._generate_struct_class_properties(ns, data_type)
        self.emit()

    def _generate_union_class(self, ns, data_type):
        # type: (ApiNamespace, Union) -> None
        self.emit(self._class_declaration_for_type(ns, data_type))
        with self.indent(), emit_pass_if_nothing_emitted(self):
            self._generate_union_class_vars(ns, data_type)
            self._generate_union_class_is_set(data_type)
            self._generate_union_class_variant_creators(ns, data_type)
            self._generate_union_class_get_helpers(ns, data_type)
        self.emit()

    def _generate_union_class_vars(self, ns, data_type):
        # type: (ApiNamespace, Union) -> None
        lineno = self.lineno

        # Generate stubs for class variables so that IDEs like PyCharms have an
        # easier time detecting their existence.
        for field in data_type.fields:
            if is_void_type(field.data_type):
                field_name = fmt_var(field.name)
                field_type = class_name_for_data_type(data_type, ns)
                self.emit('{field_name} = ...  # type: {field_type}'.format(
                    field_name=field_name,
                    field_type=field_type,
                ))

        if lineno != self.lineno:
            self.emit()

    def _generate_union_class_is_set(self, union):
        # type: (Union) -> None
        for field in union.fields:
            field_name = fmt_func(field.name)
            self.emit('def is_{}(self) -> bool: ...'.format(field_name))
            self.emit()

    def _generate_union_class_variant_creators(self, ns, data_type):
        # type: (ApiNamespace, Union) -> None
        """
        Generate the following section in the 'union Shape' example:
        @classmethod
        def circle(cls, val: float) -> Shape: ...
        """
        union_type = class_name_for_data_type(data_type)

        for field in data_type.fields:
            if not is_void_type(field.data_type):
                field_name_reserved_check = fmt_func(field.name, True)
                val_type = self.map_stone_type_to_pep484_type(ns, field.data_type)

                self.emit('@classmethod')
                self.emit('def {field_name}(cls, val: {val_type}) -> {union_type}: ...'.format(
                    field_name=field_name_reserved_check,
                    val_type=val_type,
                    union_type=union_type,
                ))
                self.emit()

    def _generate_union_class_get_helpers(self, ns, data_type):
        # type: (ApiNamespace, Union) -> None
        """
        Generates the following section in the 'union Shape' example:
        def get_circle(self) -> float: ...
        """
        for field in data_type.fields:
            field_name = fmt_func(field.name)

            if not is_void_type(field.data_type):
                # generate getter for field
                val_type = self.map_stone_type_to_pep484_type(ns, field.data_type)

                self.emit('def get_{field_name}(self) -> {val_type}: ...'.format(
                    field_name=field_name,
                    val_type=val_type,
                ))
                self.emit()

    def _generate_alias_definition(self, namespace, alias):
        # type: (ApiNamespace, Alias) -> None
        unwrapped_dt, _ = unwrap_aliases(alias)
        if is_user_defined_type(unwrapped_dt):
            # If the alias is to a composite type, we want to alias the
            # generated class as well.
            self.emit('{} = {}'.format(
                alias.name,
                class_name_for_data_type(alias.data_type, namespace)))

    def _class_declaration_for_type(self, ns, data_type):
        # type: (ApiNamespace, typing.Union[Struct, Union]) -> typing.Text
        assert is_user_defined_type(data_type), \
            'Expected struct, got %r' % type(data_type)
        if data_type.parent_type:
            extends = class_name_for_data_type(data_type.parent_type, ns)
        else:
            if is_union_type(data_type):
                # Use a handwritten base class
                extends = 'bb.Union'
            else:
                extends = 'object'
        return 'class {}({}):'.format(
            class_name_for_data_type(data_type), extends)

    def _generate_struct_class_init(self, ns, struct):
        # type: (ApiNamespace, Struct) -> None
        args = []
        for field in struct.all_fields:
            field_name_reserved_check = fmt_var(field.name, True)
            field_type = self.map_stone_type_to_pep484_type(ns, field.data_type)
            args.append(
                "{field_name}: {field_type} = ...".format(
                    field_name=field_name_reserved_check,
                    field_type=field_type,
                )
            )

        self.generate_multiline_list(
            before='def __init__',
            items=["self"] + args,
            after=' -> None: ...')

    property_template = textwrap.dedent(
        """
        @property
        def {field_name}(self) -> {field_type}: ...

        @{field_name}.setter
        def {field_name}(self, val: {field_type}) -> None: ...

        @{field_name}.deleter
        def {field_name}(self) -> None: ...
        """)

    def _generate_struct_class_properties(self, ns, struct):
        # type: (ApiNamespace, Struct) -> None
        to_emit = []  # type: typing.List[typing.Text]
        for field in struct.all_fields:
            field_name_reserved_check = fmt_func(field.name, check_reserved=True)
            field_type = self.map_stone_type_to_pep484_type(ns, field.data_type)

            to_emit.extend(
                self.property_template.format(
                    field_name=field_name_reserved_check,
                    field_type=field_type
                ).split("\n")
            )

        for s in to_emit:
            self.emit(s)

    def _get_pep_484_type_mapping_callbacks(self):
        # type: () -> OverrideDefaultTypesDict
        """
        Once-per-instance, generate a mapping from
        "List" -> return pep4848-compatible List[SomeType]
        "Nullable" -> return pep484-compatible Optional[SomeType]

        This is per-instance because we have to also call `self._register_typing_import`, because
        we need to potentially import some things.
        """
        def upon_encountering_list(ns, data_type, override_dict):
            # type: (ApiNamespace, DataType, OverrideDefaultTypesDict) -> str
            self.import_tracker._register_typing_import("List")
            return str("List[{}]").format(
                map_stone_type_to_python_type(ns, data_type, override_dict)
            )

        def upon_encountering_map(ns, key_data_type, value_data_type, override_dict):
            # type: (ApiNamespace, DataType, DataType, OverrideDefaultTypesDict) -> str
            self.import_tracker._register_typing_import("Dict")
            return str("Dict[{}, {}]").format(
                map_stone_type_to_python_type(ns, key_data_type, override_dict),
                map_stone_type_to_python_type(ns, value_data_type, override_dict)
            )

        def upon_encountering_nullable(ns, data_type, override_dict):
            # type: (ApiNamespace, DataType, OverrideDefaultTypesDict) -> str
            self.import_tracker._register_typing_import("Optional")
            return str("Optional[{}]").format(
                map_stone_type_to_python_type(ns, data_type, override_dict)
            )

        def upon_encountering_timestamp(
                ns, data_type, override_dict
        ):  # pylint: disable=unused-argument
            # type: (ApiNamespace, DataType, OverrideDefaultTypesDict) -> str
            self.import_tracker._register_adhoc_import("import datetime")
            return map_stone_type_to_python_type(ns, data_type)

        callback_dict = {
            List: upon_encountering_list,
            Map: upon_encountering_map,
            Nullable: upon_encountering_nullable,
            Timestamp: upon_encountering_timestamp,
        }  # type: OverrideDefaultTypesDict
        return callback_dict

    def map_stone_type_to_pep484_type(self, ns, data_type):
        # type: (ApiNamespace, DataType) -> str
        assert self._pep_484_type_mapping_callbacks
        return map_stone_type_to_python_type(ns, data_type,
                                             override_dict=self._pep_484_type_mapping_callbacks)

    def _generate_imports_needed_for_typing(self):
        # type: () -> None
        if self.import_tracker.cur_namespace_typing_imports:
            self.emit("")
            self.emit('from typing import (')
            with self.indent():
                for to_import in sorted(self.import_tracker.cur_namespace_typing_imports):
                    self.emit("{},".format(to_import))
            self.emit(')')

        if self.import_tracker.cur_namespace_adhoc_imports:
            self.emit("")
            for to_import in self.import_tracker.cur_namespace_adhoc_imports:
                self.emit(to_import)
