"""
A command-line interface for BabelAPI.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import imp
import logging
import os
import sys
import traceback

from .babel.exception import InvalidSpec
from .babel.tower import TowerOfBabel
from .compiler import Compiler, GeneratorException

# The parser for command line arguments
_cmdline_parser = argparse.ArgumentParser(description='BabelAPI')
_cmdline_parser.add_argument(
    '-v',
    '--verbose',
    action='count',
    help='Print debugging statements.',
)
_cmdline_parser.add_argument(
    'generator',
    type=str,
    help='Specify the path to a generator. It must have a .babelg.py extension.',
)
_cmdline_parser.add_argument(
    'spec',
    nargs='+',
    type=str,
    help='Path to API specifications. Each must have a .babel extension.',
)
_cmdline_parser.add_argument(
    'output',
    type=str,
    help='The folder to save generated files to.',
)
_cmdline_parser.add_argument(
    '--clean-build',
    action='store_true',
    help='The path to the template SDK for the target language.',
)

def main():
    """The entry point for the program."""

    args = _cmdline_parser.parse_args()
    debug = False
    if args.verbose is None:
        logging_level = logging.WARNING
    elif args.verbose == 1:
        logging_level = logging.INFO
    elif args.verbose == 2:
        logging_level = logging.DEBUG
        debug = True
    else:
        print('error: I can only be so garrulous, try -vv.', file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging_level)

    if args.spec[0].startswith('+') and args.spec[0].endswith('.py'):
        # Hack: Special case for defining a spec in Python for testing purposes
        # Use this if you want to define a Babel spec using a Python module.
        # The module should should contain an api variable that references a
        # :class:`babelapi.api.Api` object.
        try:
            api = imp.load_source('api', args.api[0]).api
        except ImportError as e:
            print('error: Could not import API description due to:',
                  e, file=sys.stderr)
            sys.exit(1)
    else:
        specs = []
        for spec_path in args.spec:
            if not spec_path.endswith('.babel'):
                print("error: Specification '%s' must have a .babel extension."
                      % spec_path,
                      file=sys.stderr)
                sys.exit(1)
            elif not os.path.exists(spec_path):
                print("error: Specification '%s' cannot be found." % spec_path,
                      file=sys.stderr)
                sys.exit(1)
            else:
                with open(spec_path) as f:
                    specs.append((spec_path, f.read()))

        # TODO: Needs version
        tower = TowerOfBabel(specs, debug=debug)

        try:
            api = tower.parse()
        except InvalidSpec as e:
            print('%s:%s: error: %s' % (e.path, e.lineno, e.msg), file=sys.stderr)
            if debug:
                print('A traceback is included below in case this is a bug in '
                      'Babel.\n', traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
        if api is None:
            print('You must fix the above parsing errors for generation to '
                  'continue.', file=sys.stderr)
            sys.exit(1)

    if not os.path.exists(args.generator):
        print("error: Generator '%s' cannot be found." % args.generator,
              file=sys.stderr)
        sys.exit(1)
    elif not os.path.isfile(args.generator):
        print("error: Generator '%s' must be a file." % args.generator,
              file=sys.stderr)
        sys.exit(1)
    elif not Compiler.is_babel_generator(args.generator):
        print("%s: error: Generator '%s' must have a .babelg.py extension." %
              args.generator, file=sys.stderr)
        sys.exit(1)
    else:
        try:
            generator_module = imp.load_source('user_generator', args.generator)
        except:
            print('%s: error: Importing generator module raised an exception:' %
                  args.generator, file=sys.stderr)
            raise

    c = Compiler(
        api,
        generator_module,
        args.output,
        clean_build=args.clean_build,
    )
    try:
        c.build()
    except GeneratorException as e:
        print('%s: error: %s raised an exception:\n%s' %
              (args.generator, e.generator_name, e.traceback),
              file=sys.stderr)
        sys.exit(1)

    if not sys.argv[0].endswith('babelapi'):
        # If we aren't running from an entry_point, then return api to make it
        # easier to do debugging.
        return api

if __name__ == '__main__':
    # Assign api variable for easy debugging from a Python console
    api = main()
