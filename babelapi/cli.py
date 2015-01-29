"""
A command-line interface for BabelAPI.
"""

import argparse
import imp
import logging
import os
import sys
import traceback

from babelapi.compiler import Compiler
from babelapi.babel.tower import InvalidSpec, TowerOfBabel

def main():
    """The entry point for the program."""

    cmdline_parser = argparse.ArgumentParser(description='BabelAPI')
    cmdline_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Print debugging statements.',
    )
    cmdline_parser.add_argument(
        'generator',
        type=str,
        help='Specify a pre-packaged generator (only "python" right now), or '
             'the path to a custom generator (.babelg.py).',
    )
    cmdline_parser.add_argument(
        'spec',
        nargs='+',
        type=str,
        help='Path to API specifications (*.babel).',
    )
    cmdline_parser.add_argument(
        'output',
        type=str,
        help='The folder to save generated files to.',
    )

    cmdline_parser.add_argument(
        '--clean-build',
        action='store_true',
        help='The path to the template SDK for the target language.',
    )

    args = cmdline_parser.parse_args()
    debug = args.verbose
    if debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(level=logging_level)

    if args.spec[0].startswith('+') and args.spec[0].endswith('.py'):
        # Hack: Special case for defining a spec in Python for testing purposes
        try:
            api = imp.load_source('api', args.api[0]).api
        except ImportError as e:
            print >> sys.stderr, 'Could not import API description due to:', e
            sys.exit(1)
    else:
        # TODO: Needs version
        tower = TowerOfBabel(args.spec, debug=debug)
        try:
            api = tower.parse()
        except InvalidSpec as e:
            print >> sys.stderr, 'Specification had error(s). You must fix ' \
                'these to continue:\n'
            print >> sys.stderr, e, '\n'
            if debug:
                print >> sys.stderr, 'A traceback is included below in case ' \
                    'this is a bug in Babel.\n', traceback.format_exc()
            else:
                print >> sys.stderr, 'If the error is not clear, try using ' \
                                     'the -v flag.'
            sys.exit(1)
        if api is None:
            print >> sys.stderr, \
                'You must fix the above parsing errors for generation to continue.'
            sys.exit(1)

    # Here we support two ways of specifying a generator. Either a name of a
    # generator, which assumes it has been pre-packaged with babelapi, or a
    # path to a Python module with a generator class defined within.
    if args.generator == 'python':
        generator = os.path.join(os.path.dirname(__file__),
                                 'generator/target/python/python.babelg.py')
    else:
        generator = args.generator

    c = Compiler(
        api,
        generator,
        args.output,
        clean_build=args.clean_build,
    )
    c.build()

    if not sys.argv[0].endswith('babelapi'):
        # If we aren't running from an entry_point, then return api to make it
        # easier to do debugging.
        return api

if __name__ == '__main__':
    # Assign api variable for easy debugging from a Python console
    api = main()
