"""
A command-line interface for BabelAPI.
"""

import argparse
import imp
import logging
import os
import sys

from babelapi.compiler import Compiler
from babelapi.babel.tower import TowerOfBabel

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
        help='The path to the generator (*.py).',
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
        api = tower.parse()

    c = Compiler(
        api,
        args.generator,
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
