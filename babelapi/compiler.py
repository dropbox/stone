from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import logging
import imp
import inspect
import os
import re
import shutil

from babelapi.generator import Generator

class UnknownGenerator(Exception): pass
class UnknownSourceType(Exception): pass
class MissingBabelPreamble(Exception): pass

class Compiler(object):
    """
    Takes a Babel API representation and generator path as input, and generates
    output files into the output folder.
    """

    first_line_re = re.compile('babelapi\((?P<generator>\w+)\)')
    template_extension = '.babelt'
    generator_extension = '.babelg'

    def __init__(self,
                 api,
                 generator_path,
                 build_path,
                 clean_build=False):
        """
        Creates a Compiler.

        :param babelapi.api.Api api: A Babel description of the API.
        :param str generator_path: Path to generator.
        :param str build_path: Location to save compiled sources to. If None,
            source files are compiled into the same directories.
        :param bool clean_build: If True, the build_path is removed before
            source files are compiled into them.
        """
        self._logger = logging.getLogger('babelapi.compiler')

        self.api = api
        self.generator_path = generator_path
        self.build_path = build_path

        # Remove existing build directory if it's a clean build
        if clean_build and os.path.exists(self.build_path):
            logging.info('Cleaning existing build directory %s...',
                         self.build_path)
            shutil.rmtree(self.build_path)

    def build(self):
        """Creates outputs. Outputs are files made by a generator."""
        if os.path.exists(self.build_path) and not os.path.isdir(self.build_path):
            self._logger.error('Output path must be a folder if it already exists')
            return

        if os.path.exists(self.generator_path):
            if os.path.isdir(self.generator_path):
                self._logger.error('Folder specified as generator at %s',
                                   self.generator_path)
            else:
                self._logger.info('Found generator at %s', self.generator_path)
                Compiler._mkdir(self.build_path)
                self._process_file(self.generator_path)
        else:
            self._logger.error('Could not find generator at %s', self.generator_path)

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
    def _is_babel_generator(cls, path):
        """
        Returns True if the file name matches the format of a babel generator,
        ie. its inner extension of "babelg". For example: xyz.babelg.py
        """
        path_without_ext, first_ext = os.path.splitext(path)
        _, second_ext = os.path.splitext(path_without_ext)
        return second_ext == cls.generator_extension

    @staticmethod
    def _get_babel_template_target_file(path):
        """
        Returns the path that a template should compile to.
        """
        path_without_ext, first_ext = os.path.splitext(path)
        path_without_babel_ext, second_ext = os.path.splitext(path_without_ext)
        return path_without_babel_ext + first_ext

    def _process_file(self, source_path):
        """Renders a source file into its final form."""

        if self._is_babel_generator(source_path):
            self._logger.info('Running generator at %s', source_path)
            # If there's no preamble, then we assume this is a Python file
            # that defines a generator.
            generator_module = imp.load_source('user_generator', source_path)
            try:
                os.remove(source_path + 'c')
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

            for attr_key in dir(generator_module):
                attr_value = getattr(generator_module, attr_key)
                if (inspect.isclass(attr_value)
                        and issubclass(attr_value, Generator)
                        and not inspect.isabstract(attr_value)):
                    generator = attr_value(self.build_path)
                    try:
                        generator.generate(self.api)
                    except:
                        # Tell the user that this isn't a bug with the babel
                        # parser but a bug with the generator they are using.
                        self._logger.error(
                            'Generator (%s) failed with an error:\n' %
                            generator.__class__.__name__)
                        raise
        else:
            raise UnknownSourceType(source_path)
