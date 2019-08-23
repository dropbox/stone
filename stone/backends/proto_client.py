from __future__ import unicode_literals

from stone.backend import CodeBackend
from stone.ir import(
    Struct,
)
from stone.backends.proto_type_mapping import map_stone_type_to_proto, is_primitive_data
from stone.backends.proto_helpers import(
    obj_end,
    message_fmt,
    expr_eq,
    expr_st,
)

import importlib
argparse = importlib.import_module(str('argparse'))

_cmdline_parser = argparse.ArgumentParser(prog='proto-client-backend')
_cmdline_parser.add_argument(
    '-m',
    '--module-name',
    required=True,
    type=str,
    help=('The name(without extension) of the protobuf file to generate.')
)

class ProtoBackend(CodeBackend):

    cmdline_parser = _cmdline_parser

    def generate(self, api):
        with self.output_to_relative_path('%s.proto' % self.args.module_name):
            for namespace in api.namespaces.values():
                self._create_package(namespace.name)
                self._generate_types(namespace)

    def _create_package(self, val):
        self.emit('syntax = "proto3";')
        self.emit('package ' + val + ';')
        self.emit()

    def _generate_types(self, namespace):
        for data in namespace.data_types:
            self._create_proto_data(data)

    def _create_proto_data(self, data):
        if isinstance(data, Struct):
            self._generate_message(data)

    def _generate_message(self, data):

        self.emit(message_fmt(data.name))

        with self.indent():
            for counter, field in enumerate(data.fields):
                #check if nested userdefined dataytpe
                if not is_primitive_data(field.data_type):
                    typ = field.data_type.name

                else:
                    typ = map_stone_type_to_proto(field.data_type)
                self.emit(expr_eq(typ, field.name, str(counter)))

        self.emit(obj_end())
        self.emit()