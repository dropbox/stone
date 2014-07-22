"""
A command-line interface for BabelSDK.
"""

import argparse
import imp
import logging
import os
import sys

from babelsdk.compiler import Compiler
from babelsdk.babel.tower import TowerOfBabel

def main():
    """The entry point for the program."""

    cmdline_parser = argparse.ArgumentParser(description='BabelSDK')
    cmdline_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Print debugging statements.'
    )
    cmdline_parser.add_argument(
        '-t',
        '--target-path',
        type=str,
        help='The path to save compiled source files to.'
    )
    cmdline_parser.add_argument('api', nargs='+', type=str, help='Babel files describing the API.')
    cmdline_parser.add_argument(
        'path',
        help='The path to the template SDK for the target language.',
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

    logging.info('Analyzing these Babel files: %r', args.api)

    if args.api[0].endswith('.py'):
        # Special case if the API description file ends in .py
        # Assume it's an internal representation used for testing.
        try:
            api = imp.load_source('api', args.api[0]).api
        except ImportError as e:
            print >> sys.stderr, 'Could not import API description due to:', e
            sys.exit(1)
    else:
        # TODO: Needs version
        tower = TowerOfBabel(args.api, debug=debug)
        api = tower.parse()

    if args.target_path:
        build_path = os.path.join(args.target_path, os.path.basename(args.path))
    else:
        build_path = None

    c = Compiler(
        api,
        args.path,
        build_path,
        clean_build=args.clean_build,
    )
    c.build()

    return api

if __name__ == '__main__':
    # Assign api variable for easy debugging from a Python console
    api = main()
