import base64
import datetime
import json
import unittest

from babelapi.generator.target.python import (
    babel_data_types as dt
)
from babelapi.generator.target.python.babel_serializers import (
    JsonEncoder,
    JsonDecoder,
)

class TestPythonGen(unittest.TestCase):
    """
    Tests the Python Generator.
    TODO(kelkabany): Currently tests only the dependencies, and not the
        generated code.
    """

    def test_string_data_type(self):
        s = dt.String(min_length=1, max_length=5, pattern='[A-z]+')
        # Not a string
        self.assertRaises(dt.ValidationError, lambda: s.validate(1))
        # Too short
        self.assertRaises(dt.ValidationError, lambda: s.validate(''))
        # Too long
        self.assertRaises(dt.ValidationError, lambda: s.validate('a'*6))
        # Doesn't pass regex
        self.assertRaises(dt.ValidationError, lambda: s.validate('#'))
        # Passes
        s.validate('a')

    def test_boolean_data_type(self):
        b = dt.Boolean()
        b.validate(True)
        b.validate(False)
        self.assertRaises(dt.ValidationError, lambda: b.validate(1))

    def test_integer_data_type(self):
        i = dt.UInt32(min_value=10, max_value=100)
        # Not an integer
        self.assertRaises(dt.ValidationError, lambda: i.validate(1.4))
        # Too small
        self.assertRaises(dt.ValidationError, lambda: i.validate(1))
        # Too large
        self.assertRaises(dt.ValidationError, lambda: i.validate(101))
        # Passes
        i.validate(50)

        # min_value is less than the default for the type
        self.assertRaises(ValueError, lambda: dt.UInt32(min_value=-3))
        # non-sensical min_value
        self.assertRaises(AssertionError, lambda: dt.UInt32(min_value=1.3))

    def test_binary_data_type(self):
        b = dt.Binary(min_length=1, max_length=10)
        # Not a valid binary type
        self.assertRaises(dt.ValidationError, lambda: b.validate(u'asdf'))
        # Too short
        self.assertRaises(dt.ValidationError, lambda: b.validate(''))
        # Too long
        self.assertRaises(dt.ValidationError, lambda: b.validate('\x00'*11))
        # Passes
        b.validate('\x00')

    def test_timestamp_data_type(self):
        t = dt.Timestamp('%a, %d %b %Y %H:%M:%S +0000')
        self.assertRaises(ValueError, lambda: t.validate('abcd'))
        t.validate(datetime.datetime.utcnow())

    def test_list_data_type(self):
        l = dt.List(dt.String(), min_items=1, max_items=10)
        # Not a valid list type
        self.assertRaises(dt.ValidationError, lambda: l.validate('a'))
        # Too short
        self.assertRaises(dt.ValidationError, lambda: l.validate([]))
        # Too long
        self.assertRaises(dt.ValidationError, lambda: l.validate([1]*11))
        # Not a valid string type
        self.assertRaises(dt.ValidationError, lambda: l.validate([1]))
        # Passes
        l.validate(['a'])

    def test_struct_data_type(self):
        class C(object):
            _fields_ = [('f', dt.String())]
            f = None
        s = dt.Struct(C)
        self.assertRaises(dt.ValidationError, lambda: s.validate(object()))

    def test_any_data_type(self):
        a = dt.Any()
        a.validate(object())

    def test_json_encoder(self):
        self.assertEqual(JsonEncoder.encode(dt.String(), 'abc'), json.dumps('abc'))
        self.assertEqual(JsonEncoder.encode(dt.UInt32(), 123), json.dumps(123))
        self.assertEqual(JsonEncoder.encode(dt.Boolean(), True), json.dumps(True))
        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow()
        self.assertEqual(JsonEncoder.encode(dt.Timestamp('%a, %d %b %Y %H:%M:%S +0000'), now),
                         json.dumps(now.strftime(f)))
        b = '\xff' * 5
        self.assertEqual(JsonEncoder.encode(dt.Binary(), b), json.dumps(base64.b64encode(b)))

    def test_json_decoder(self):
        self.assertEqual(JsonDecoder.decode(dt.String(), json.dumps('abc')), 'abc')
        self.assertEqual(JsonDecoder.decode(dt.UInt32(), json.dumps(123)), 123)
        self.assertEqual(JsonDecoder.decode(dt.Boolean(), json.dumps(True)), True)
        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow().replace(microsecond=0)
        self.assertEqual(JsonDecoder.decode(dt.Timestamp('%a, %d %b %Y %H:%M:%S +0000'),
                                            json.dumps(now.strftime(f))),
                         now)
        b = '\xff' * 5
        self.assertEqual(JsonDecoder.decode(dt.Binary(), json.dumps(base64.b64encode(b))), b)
