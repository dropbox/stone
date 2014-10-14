import logging
import os

class Generator(object):
    def __init__(self, api):
        self.api = api
        self._logger = logging.getLogger('bablesdk.generator.%s'
                                         % self.__class__.__name__)

    def render(self, extension, text):
        raise NotImplemented

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
import re
import textwrap

class CodeGenerator(object):

    __metaclass__ = ABCMeta

    # Can be overridden by a subclass
    tabs_for_indents = False

    def __init__(self, api, target_folder_path):
        self._logger = logging.getLogger('bablesdk.generator.%s'
                                         % self.__class__.__name__)
        self.api = api
        self.target_folder_path = target_folder_path
        # Output is a list of strings that should be concatenated together for
        # the final output.
        self.output = []
        self.cur_indent = 0

    @contextmanager
    def indent(self, dent=None):
        """
        For the duration of the context manager, all indents will be further
        indented by dent. Dent is in units of spaces or tabs depending on the
        value of the class variable tabs_for_indents.
        """
        assert dent != 0, 'Cannot specify relative indent of 0'
        if dent is None:
            if self.tabs_for_indents:
                dent = 1
            else:
                dent = 4
        self.cur_indent += dent
        yield
        self.cur_indent -= dent

    def make_indent(self):
        """Returns a string representing an indent. Indents can be either
        spaces or tabs, depending on the value of the class variable
        tabs_for_indents."""
        if self.tabs_for_indents:
            return '\t' * self.cur_indent
        else:
            return ' ' * self.cur_indent

    def emit(self, s):
        """Adds the input string to the output buffer."""
        self.output.append(s)

    def emit_indent(self):
        """Adds an indent into the output buffer."""
        self.emit(self.make_indent())

    def emit_line(self, s):
        """Adds an indent, then the input string, and lastly a newline to the
        output buffer. If you want the input string to potentially span across
        multiple lines, see :func:`emit_string_wrap`."""
        self.emit_indent()
        self.emit(s)
        self.emit('\n')

    def emit_empty_line(self):
        """Adds a newline to the output buffer."""
        self.emit('\n')

    def emit_string_wrap(self, s, prefix='', width=80):
        """
        Adds the input string to the output buffer with wrapping.

        Args:
            s: The input string to wrap.
            prefix: The string to prepend to every line of the wrapped string.
                Does not include indenting in the prefix as those are injected
                automatically on every line.
            width: The target width of each line including indentation and text.
        """
        indent = self.make_indent() + prefix
        self.emit(textwrap.fill(s,
                                initial_indent=indent,
                                subsequent_indent=indent,
                                width=80))

    def _filter_out_none_valued_keys(self, d):
        """Given a dict, returns a new dict with all the same key/values except
        for keys that had values of None."""
        new_d = {}
        for k, v in d.iteritems():
            if v is not None:
                new_d[k] = v
        return new_d

    @contextmanager
    def output_to_relative_path(self, relative_path):
        """
        Sets up generator so that all emits are directed towards the new file
        created at :param:`relative_path`.

        Clears output buffer on enter, and on exit.
        """
        full_path = os.path.join(self.target_folder_path, relative_path)
        self._logger.info('Auto-generating %s', full_path)
        self.output = []
        yield
        with open(full_path, 'w') as f:
            f.write(''.join(self.output))
        self.output = []

    @abstractmethod
    def generate(self):
        """Subclasses should override this method. It's the entry point for
        all code generation given the api description."""
        raise NotImplemented


class CodeGeneratorMonolingual(CodeGenerator):
    """Identical to CodeGenerator, except that an additional attribute `lang`
    exists."""

    # An instance of a :class:`babelsdk.lang.lang.TargetLanguage` object.
    lang = None

    def __init__(self, api, target_folder_path):
        assert self.lang, 'Language must be specified'
        super(CodeGeneratorMonolingual, self).__init__(api, target_folder_path)
