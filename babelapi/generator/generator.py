from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
import logging
import os
import textwrap

class Generator(object):
    """
    The parent class for all generators. All generators should extend this
    class to be recognized as such.

    You will want to implement the generate() function to do the generation
    that you need.

    Here's roughly what you need to do in generate().
    1. Use the context manager output_to_relative_path() to specify an output file.

        with output_to_relative_path('generated_code.py'):
            ...

    2. Use the family of emit*() functions to write to the output file.
    """

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
        self.lineno = 1
        self.cur_indent = 0

    @abstractmethod
    def generate(self):
        """Subclasses should override this method. It's the entry point for
        all code generation given the api description."""
        raise NotImplemented

    @contextmanager
    def output_to_relative_path(self, relative_path):
        """
        Sets up generator so that all emits are directed towards the new file
        created at :param:`relative_path`.

        Clears output buffer on enter, and on exit.
        """
        full_path = os.path.join(self.target_folder_path, relative_path)
        self._logger.info('Generating %s', full_path)
        self.output = []
        yield
        with open(full_path, 'w') as f:
            f.write(''.join(self.output))
        self.output = []

    @contextmanager
    def indent(self, dent=None):
        """
        For the duration of the context manager, indentation will be increased
        by dent. Dent is in units of spaces or tabs depending on the value of
        the class variable tabs_for_indents.
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

    @contextmanager
    def block(self, header='', dent=None, delim=('{','}')):
        if header:
            self.emit_line('{} {}'.format(header, delim[0]))
        else:
            self.emit_line(delim[0])
        self.emit_empty_line()

        with self.indent(dent):
            yield

        self.emit_line(delim[1])

    @contextmanager
    def indent_to_cur_col(self):
        """
        For the duration of the context manager, indentation will be set to the
        current column marked by the "cursor". The cursor is what column of the
        current line the next emit call would begin writing at.
        """
        dent = 0
        for s in self.output[::-1]:
            index = s.rfind('\n')
            if index == -1:
                dent += len(s)
            else:
                dent += len(s) - index - 1
                break
        dent_diff = dent - self.cur_indent
        self.cur_indent += dent_diff
        yield
        self.cur_indent -= dent_diff

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
        self.lineno += s.count('\n')
        self.output.append(s)

    def emit_indent(self):
        """Adds an indent into the output buffer."""
        self.emit(self.make_indent())

    def emit_line(self, s, trailing_newline=True):
        """Adds an indent, then the input string, and lastly a newline to the
        output buffer. If you want the input string to potentially span across
        multiple lines, see :func:`emit_string_wrap`."""
        self.emit_indent()
        self.emit(s)
        if trailing_newline:
            self.emit('\n')

    def emit_empty_line(self):
        """Adds a newline to the output buffer."""
        self.emit('\n')

    def emit_wrapped_lines(self, s, prefix='', width=80, trailing_newline=True, first_line_prefix=True):
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
        if first_line_prefix:
            initial_indent = indent
        else:
            initial_indent = self.make_indent()

        self.emit(textwrap.fill(s,
                                initial_indent=initial_indent,
                                subsequent_indent=indent,
                                width=80))
        if trailing_newline:
            self.emit('\n')

class CodeGenerator(Generator):
    """
    Extend this instead of :class:`Generator` when generating source code.
    Contains helper functions specific to code generation.
    """

    def _filter_out_none_valued_keys(self, d):
        """Given a dict, returns a new dict with all the same key/values except
        for keys that had values of None."""
        new_d = {}
        for k, v in d.iteritems():
            if v is not None:
                new_d[k] = v
        return new_d

    def _generate_func_arg_list(self, args, compact=True):
        """
        Given a list of arguments to a function, emits the args, one per line
        with a trailing comma. The arguments are enclosed in parentheses making
        this convenient way to create argument lists in function prototypes and
        calls.

        Args:
            args: List of strings where each string is an argument.
            compact: In compact mode, the enclosing parentheses are on the same
                lines as the first and last argument.
        """
        self.emit('(')
        if len(args) == 0:
            self.emit(')')
            return
        elif len(args) == 1:
            self.emit(args[0])
            self.emit(')')
        else:
            if compact:
                with self.indent_to_cur_col():
                    args = args[:]
                    self.emit(args.pop(0))
                    self.emit(',')
                    self.emit_empty_line()
                    for (i, arg) in enumerate(args):
                        if i == len(args) - 1:
                            self.emit_line(arg, trailing_newline=False)
                        else:
                            self.emit_line(arg + ',')
                    self.emit(')')
            else:
                self.emit_empty_line()
                with self.indent():
                    for arg in args:
                        self.emit_line(arg + ',')
                self.emit_indent()
                self.emit(')')

class CodeGeneratorMonolingual(CodeGenerator):
    """Identical to CodeGenerator, except that an additional attribute `lang`
    exists. You can set this to a TargetLanguage object for easy access to
    language-specific convenience functions."""

    # An instance of a :class:`babelapi.lang.lang.TargetLanguage` object.
    lang = None

    def __init__(self, api, target_folder_path):
        assert self.lang, 'Language must be specified'
        super(CodeGeneratorMonolingual, self).__init__(api, target_folder_path)
