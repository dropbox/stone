from __future__ import unicode_literals
from stone.backend import CodeBackend

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

    def _create_package(self, val):
        self.emit('syntax = "proto3";')
        self.emit('package ' + val + ';')
