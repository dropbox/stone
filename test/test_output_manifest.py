import os
import tempfile
import types
import unittest

from stone.backend import Backend, CodeBackend
from stone.backends.swift import SwiftBaseBackend
from stone.compiler import Compiler


class TestOutputManifest(unittest.TestCase):

    def _build_manifest(self, backend_cls):
        module = types.ModuleType('manifest_backend')
        setattr(module, backend_cls.__name__, backend_cls)

        with tempfile.TemporaryDirectory() as output_root:
            compiler = Compiler(
                None,
                module,
                [],
                output_root,
                output_manifest=True)
            compiler.build()
            existing_files = []
            for root, _, file_names in os.walk(output_root):
                for file_name in file_names:
                    existing_files.append(
                        os.path.relpath(os.path.join(root, file_name), output_root))
            return compiler.output_manifest(), sorted(existing_files)

    def test_output_to_relative_path_records_without_writing(self):

        class ManifestBackend(CodeBackend):
            preserve_aliases = True

            def generate(self, api):
                with self.output_to_relative_path('Generated.py'):
                    self.emit('generated = True')

        manifest, existing_files = self._build_manifest(ManifestBackend)

        self.assertEqual(manifest, ['Generated.py'])
        self.assertEqual(existing_files, [])

    def test_copy_to_path_records_destination_without_copying(self):
        with tempfile.NamedTemporaryFile() as source_file:

            class CopyBackend(Backend):
                preserve_aliases = True
                src_path = source_file.name

                def generate(self, api):
                    resources_path = os.path.join(self.target_folder_path, 'Resources')
                    os.makedirs(resources_path)
                    self.copy_to_path(self.src_path, resources_path)

            manifest, existing_files = self._build_manifest(CopyBackend)

        self.assertEqual(manifest, ['Resources/{}'.format(os.path.basename(source_file.name))])
        self.assertEqual(existing_files, [])

    def test_swift_output_records_without_writing(self):

        class SwiftBackend(SwiftBaseBackend):
            preserve_aliases = True

            def generate(self, api):
                self._write_output_in_target_folder('final class Generated {}', 'Generated.swift')

        manifest, existing_files = self._build_manifest(SwiftBackend)

        self.assertEqual(manifest, ['Generated.swift'])
        self.assertEqual(existing_files, [])


if __name__ == '__main__':
    unittest.main()
