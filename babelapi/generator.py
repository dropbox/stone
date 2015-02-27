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

    The target_folder_path attribute is the path to the folder where all
    generated files should be created.
    """

    __metaclass__ = ABCMeta

    # Can be overridden by a subclass
    tabs_for_indents = False

    def __init__(self, target_folder_path):
        """
        Args:
            target_folder_path (str): Path to the folder where all generated
                files should be created.
        """
        self.logger = logging.getLogger('Generator<%s>' %
                                        self.__class__.__name__)
        self.target_folder_path = target_folder_path
        # Output is a list of strings that should be concatenated together for
        # the final output.
        self.output = []
        self.lineno = 1
        self.cur_indent = 0

    @abstractmethod
    def generate(self, api):
        """
        Subclasses should override this method. It's the entry point that is
        invoked by the rest of the toolchain.

        Args:
            api (babelapi.api.Api): The API specification.
        """
        raise NotImplemented

    @contextmanager
    def output_to_relative_path(self, relative_path):
        """
        Sets up generator so that all emits are directed towards the new file
        created at :param:`relative_path`.

        Clears the output buffer on enter and exit.
        """
        full_path = os.path.join(self.target_folder_path, relative_path)
        self.logger.info('Generating %s', full_path)
        self.output = []
        yield
        with open(full_path, 'w') as f:
            f.write(''.join(self.output))
        self.output = []

    def output_buffer_to_string(self):
        """Returns the contents of the output buffer as a string."""
        return ''.join(self.output)

    def clear_output_buffer(self):
        self.output = []

    @contextmanager
    def indent(self, dent=None):
        """
        For the duration of the context manager, indentation will be increased
        by dent. Dent is in units of spaces or tabs depending on the value of
        the class variable tabs_for_indents. If dent is None, indentation will
        increase by either four spaces or one tab.
        """
        assert dent is None or dent > 0, 'dent must be a whole number.'
        if dent is None:
            if self.tabs_for_indents:
                dent = 1
            else:
                dent = 4
        self.cur_indent += dent
        yield
        self.cur_indent -= dent

    def make_indent(self):
        """
        Returns a string representing the current indentation. Indents can be
        either spaces or tabs, depending on the value of the class variable
        tabs_for_indents.
        """
        if self.tabs_for_indents:
            return '\t' * self.cur_indent
        else:
            return ' ' * self.cur_indent

    def emit_raw(self, s):
        """
        Adds the input string to the output buffer. The string must end in a
        newline. It may contain any number of newline characters. No
        indentation is generated.
        """
        self.lineno += s.count('\n')
        self.output.append(s)
        if len(s) > 0 and s[-1] != '\n':
            raise AssertionError(
                'Input string to emit_raw must end with a newline.')

    def emit(self, s=''):
        """
        Adds indentation, then the input string, and lastly a newline to the
        output buffer. If s is an empty string (default) then an empty line is
        created with no indentation.
        """
        assert isinstance(s, basestring), 's must be a string type'
        assert '\n' not in s, \
            'String to emit cannot contain newline strings.'
        if s:
            self.emit_raw('%s%s\n' % (self.make_indent(), s))
        else:
            self.emit_raw('\n')

    def emit_wrapped_text(self, s, initial_prefix='', subsequent_prefix='',
            width=80, break_long_words=False, break_on_hyphens=False):
        """
        Adds the input string to the output buffer with indentation and
        wrapping. The wrapping is performed by the :func:`textwrap.fill` Python
        library function.

        Args:
            s (str): The input string to wrap.
            initial_prefix (str): The string to prepend to the first line of
                the wrapped string. Note that the current indentation is
                already added to each line.
            subsequent_prefix (str): The string to prepend to every line after
                the first. Note that the current indentation is already added
                to each line.
            width (int): The target width of each line including indentation
                and text.
            break_long_words (bool): Break words longer than width.  If false,
                those words will not be broken, and some lines might be longer
                than width.
            break_on_hyphens (bool): Allow breaking hyphenated words. If true,
                wrapping will occur preferably on whitespaces and right after
                hyphens part of compound words.
        """
        indent = self.make_indent()
        self.emit_raw(textwrap.fill(s,
                                    initial_indent=indent+initial_prefix,
                                    subsequent_indent=indent+subsequent_prefix,
                                    width=width,
                                    break_long_words=break_long_words,
                                    break_on_hyphens=break_on_hyphens,
                                    ) + '\n')

class CodeGenerator(Generator):
    """
    Extend this instead of :class:`Generator` when generating source code.
    Contains helper functions specific to code generation.
    """

    def filter_out_none_valued_keys(self, d):
        """Given a dict, returns a new dict with all the same key/values except
        for keys that had values of None."""
        new_d = {}
        for k, v in d.iteritems():
            if v is not None:
                new_d[k] = v
        return new_d

    def generate_multiline_list(self, items, before='', after='',
                delim=('(', ')'), compact=True, sep=',', skip_last_sep=False):
        """
        Given a list of items, emits one item per line.

        This is convenient for function prototypes and invocations, as well as
        for instantiating arrays, sets, and maps in some languages.

        TODO(kelkabany): A generator that uses tabs cannot be used with this
            if compact is false.

        Args:
            items (list[str]): Should contain the items to generate a list of.
            before (str): The string to come before the list of items.
            after (str): The string to follow the list of items.
            delim (str, str): The first element is added immediately following
                `before`. The second element is added prior to `after`.
            compact (bool): In compact mode, the enclosing parentheses are on
                the same lines as the first and last list item.
            sep (str): The string that follows each list item when compact is
                true. If compact is false, the separator is omitted for the
                last item.
            skip_last_sep (bool): When compact is false, whether the last line
                should have a trailing separator. Ignored when compact is true.
        """
        assert len(delim) == 2 and isinstance(delim[0], str) and \
            isinstance(delim[1], str), 'delim must be a tuple of two strings.'

        if len(items) == 0:
            self.emit(before + delim[0] + delim[1] + after)
            return
        if len(items) == 1:
            self.emit(before + delim[0] + items[0] + delim[1] + after)
            return

        if compact:
            self.emit(before + delim[0] + items[0] + sep)
            def emit_list(items):
                items = items[1:]
                for (i, item) in enumerate(items):
                    if i == len(items) - 1:
                        self.emit(item + delim[1] + after)
                    else:
                        self.emit(item + sep)
            if before or delim[0]:
                with self.indent(len(before) + len(delim[0])):
                    emit_list(items)
            else:
                emit_list(items)
        else:
            if before or delim[0]:
                self.emit(before + delim[0])
            with self.indent():
                for (i, item) in enumerate(items):
                    if i == len(items) - 1 and skip_last_sep:
                        self.emit(item)
                    else:
                        self.emit(item + sep)
            if delim[1] or after:
                self.emit(delim[1] + after)
            elif delim[1]:
                self.emit(delim[1])

    @contextmanager
    def block(self, before='', after='', delim=('{','}'), dent=None):
        """
        A context manager that emits configurable lines before and after an
        indented block of text.

        This is convenient for class and function definitions in some
        languages.

        Args:
            before (str): The string to be output in the first line which is
                not indented..
            after (str): The string to be output in the last line which is
                not indented.
            delim (str, str): The first element is added immediately following
                `before` and a space. The second element is added prior to a
                space and then `after`.
            dent (int): The amount to indent the block. If none, the default
                indentation increment is used (four spaces or one tab).
        """
        assert len(delim) == 2 and isinstance(delim[0], str) and \
            isinstance(delim[1], str), 'delim must be a tuple of two strings.'

        if before:
            self.emit('{} {}'.format(before, delim[0]))
        else:
            self.emit(delim[0])

        with self.indent(dent):
            yield

        self.emit(delim[1] + after)

class CodeGeneratorMonolingual(CodeGenerator):
    """Identical to CodeGenerator, except that an additional attribute `lang`
    exists. You can set this to a TargetLanguage object for easy access to
    language-specific convenience functions."""

    # An instance of a :class:`babelapi.lang.lang.TargetLanguage` object.
    lang = None

    def __init__(self, target_folder_path):
        assert self.lang, 'Language must be specified'
        super(CodeGeneratorMonolingual, self).__init__(target_folder_path)
