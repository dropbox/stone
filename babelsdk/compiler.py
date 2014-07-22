import logging
import os
import re
import shutil

from babelsdk.generator.jinja import Jinja2Generator

class UnknownGenerator(Exception): pass
class MissingBabelPreamble(Exception): pass

class Compiler(object):
    """
    Takes a Babel API representation as input, and outputs code in the target
    languages.
    """

    first_line_re = re.compile('babelsdk\((?P<generator>\w+)\)')
    template_extension = '.babelt'

    def __init__(self,
                 api,
                 source_path,
                 build_path,
                 clean_build=False):
        """
        Creates a Compiler.

        :param babelsdk.api.Api api: A Babel description of the API.
        :param str source_path: Path to source to be converted.
        :param str build_path: Location to save compiled sources to. If None,
            source files are compiled into the same directories.
        :param bool clean_build: If True, the build_path is removed before
            source files are compiled into them.
        """

        self._logger = logging.getLogger('babelsdk.compiler')

        self.source_path = source_path
        self.build_path = build_path

        # Remove existing build directory if it's a clean build
        if clean_build and os.path.exists(self.build_path):
            logging.info('Cleaning existing build directory %s...',
                         self.build_path)
            shutil.rmtree(self.build_path)

        self.generators = dict(
            jinja2=Jinja2Generator(api),
        )

    def build(self):
        """Replicates the file tree in the source path into the build path, but
        also renders each templated file."""

        if self.build_path:
            logging.info('Compiling path %s', self.build_path)
            Compiler._mkdir(self.build_path)
            os.path.walk(self.source_path, self._process_dir, None)
        else:
            logging.info('Compiling in place')
            os.path.walk(self.source_path, self._process_dir_in_place, None)

    @staticmethod
    def _mkdir(path):
        """
        Creates a directory at path if it doesn't exist. If it does exist,
        this function does nothing. Note that if path is a file, it will not
        be converted to a directory.
        """
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != 17:
                raise

    @classmethod
    def _is_babel_file(cls, path):
        """
        Returns True if the file name matches the format of a babel file. That
        is, the file should have an inner extension of "babel". For example:
        xyz.babel.py
        """
        path_without_ext, first_ext = os.path.splitext(path)
        _, second_ext = os.path.splitext(path_without_ext)
        return second_ext == cls.template_extension

    @staticmethod
    def _get_babel_target_file(path):
        """
        Returns the path that a Babel should compile to.
        """
        path_without_ext, first_ext = os.path.splitext(path)
        path_without_babel_ext, second_ext = os.path.splitext(path_without_ext)
        return path_without_babel_ext + first_ext

    def _process_dir(self, arg, dirname, fnames):
        """
        Walks the source directory rendering valid source files and saving them
        into the build directory.

        We check for directories that already exist in the build target so that
        we avoid deleting and recreating directories that already exist. This
        leads to a nicer experience if you have a separate terminal open in the
        build directory.
        """

        target_relative_dir_path = os.path.join(
            self.build_path,
            dirname[len(self.source_path)+1:],
        )
        Compiler._mkdir(target_relative_dir_path)

        # Remove files that no longer exist in source
        dest_fnames = os.listdir(target_relative_dir_path)
        for dest_fname in dest_fnames:
            if dest_fname not in fnames:
                os.remove(os.path.join(target_relative_dir_path, dest_fname))

        # Copy and process files from source
        for fname in fnames:
            path = os.path.join(dirname, fname)
            if os.path.isfile(path):
                target_path = os.path.join(target_relative_dir_path, fname)
                if Compiler._is_babel_file(path):
                    target_path = Compiler._get_babel_target_file(target_path)
                    self._process_file(path, target_path)
                else:
                    shutil.copyfile(path, target_path)
            else:
                # FIXME: Does not retain symlinks
                pass

    def _process_dir_in_place(self, arg, dirname, fnames):
        """
        Walks the source directory rendering valid source files.
        """

        target_relative_dir_path = os.path.join(
            self.source_path,
            dirname[len(self.source_path)+1:],
        )

        # Copy and process files from source
        for fname in fnames:
            path = os.path.join(dirname, fname)
            if os.path.isfile(path):
                target_path = os.path.join(target_relative_dir_path, fname)
                if Compiler._is_babel_file(path):
                    target_path = Compiler._get_babel_target_file(target_path)
                    self._process_file(path, target_path)

    def _process_file(self, source_path, target_path):
        """Renders a source file into its final form."""

        self._logger.info('Converting babel file %s to %s',
                          source_path, target_path)

        with open(source_path) as f:
            file_contents = f.read()

        # Read first line for preamble
        first_line = file_contents.split('\n', 1)[0]
        matches = self.first_line_re.search(first_line)
        if not matches:
            raise MissingBabelPreamble()

        # Use preamble to determine which generator to use
        generator_type = matches.group(1)
        if generator_type not in self.generators:
            raise UnknownGenerator(generator_type)

        generator = self.generators[generator_type]

        _, ext = os.path.splitext(source_path)
        rendered_contents = generator.render(ext, file_contents)

        # Inject "Generated by" message in place of the preamble
        new_first_line = first_line.replace(matches.group(0),
                                            'Generated by BabelSDK')
        rendered_contents = (new_first_line +
                             rendered_contents[len(first_line):])

        with open(target_path, 'w') as f:
            f.write(rendered_contents)
