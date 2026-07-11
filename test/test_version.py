#!/usr/bin/env python


import importlib.util
import sys
import types
import unittest
from unittest import mock

import stone


class TestVersion(unittest.TestCase):

    def test_generated_version_is_used_in_source_checkout(self):
        generated_version = types.ModuleType('stone._version')
        generated_version.__version__ = '9.8.7'

        spec = importlib.util.spec_from_file_location(
            'stone._version_test', stone.__file__)
        module = importlib.util.module_from_spec(spec)
        module.__package__ = 'stone'
        with mock.patch.dict(sys.modules, {'stone._version': generated_version}):
            spec.loader.exec_module(module)

        self.assertEqual(module.__version__, '9.8.7')


if __name__ == '__main__':
    unittest.main()
