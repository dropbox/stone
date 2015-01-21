import base64
import datetime
import json
import unittest

from babelapi.generator.target.python import (
    babel_data_types as dt
)
from babelapi.generator.target.python.babel_serializers import (
    json_encode,
    json_decode,
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
        self.assertRaises(dt.ValidationError, lambda: t.validate('abcd'))
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
        self.assertEqual(json_encode(dt.String(), 'abc'), json.dumps('abc'))
        self.assertEqual(json_encode(dt.UInt32(), 123), json.dumps(123))
        # Because a bool is a subclass of an int, ensure they aren't mistakenly
        # encoded as a true/false in JSON when an integer is the data type.
        self.assertEqual(json_encode(dt.UInt32(), True), json.dumps(1))
        self.assertEqual(json_encode(dt.Boolean(), True), json.dumps(True))
        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow()
        self.assertEqual(json_encode(dt.Timestamp('%a, %d %b %Y %H:%M:%S +0000'), now),
                         json.dumps(now.strftime(f)))
        b = '\xff' * 5
        self.assertEqual(json_encode(dt.Binary(), b), json.dumps(base64.b64encode(b)))

    def test_json_encoder_union(self):
        class S(object):
            _field_names_ = {'f'}
            _fields_ = [('f', dt.String())]
        class U(object):
            _fields_ = {'a': dt.Int64(),
                        'b': dt.Symbol(),
                        'c': dt.Struct(S),
                        'd': dt.List(dt.Int64())}
            _tag = None
            def __init__(self, tag, value=None):
                self._tag = tag
                setattr(self, '_' + tag, value)
            def get_a(self):
                return self._a
            def get_c(self):
                return self._c
            def get_d(self):
                return self._d

        U.b = U('b')

        # Test primitive variant
        u = U('a', 64)
        self.assertEqual(json_encode(dt.Union(U), u), json.dumps({'a': 64}))

        # Test symbol variant
        u = U('b')
        self.assertEqual(json_encode(dt.Union(U), u), json.dumps('b'))

        # Test struct variant
        c = S()
        c.f = 'hello'
        u = U('c', c)
        self.assertEqual(json_encode(dt.Union(U), u), json.dumps({'c': {'f': 'hello'}}))

        # Test list variant
        u = U('d', [1, 2, 3, 'a'])
        # lists should be re-validated during serialization
        self.assertRaises(dt.ValidationError, lambda: json_encode(dt.Union(U), u))
        l = [1, 2, 3, 4]
        u = U('d', [1, 2, 3, 4])
        self.assertEqual(json_encode(dt.Union(U), u), json.dumps({'d': l}))

    def test_json_decoder(self):
        self.assertEqual(json_decode(dt.String(), json.dumps('abc')), 'abc')
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.String(), json.dumps(32)))

        self.assertEqual(json_decode(dt.UInt32(), json.dumps(123)), 123)
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.UInt32(), json.dumps('hello')))

        self.assertEqual(json_decode(dt.Boolean(), json.dumps(True)), True)
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.Boolean(), json.dumps(1)))

        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow().replace(microsecond=0)
        self.assertEqual(json_decode(dt.Timestamp('%a, %d %b %Y %H:%M:%S +0000'),
                                     json.dumps(now.strftime(f))),
                         now)
        b = '\xff' * 5
        self.assertEqual(json_decode(dt.Binary(), json.dumps(base64.b64encode(b))), b)
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.Binary(), json.dumps(1)))

    def test_json_decoder_union(self):
        class S(object):
            _field_names_ = {'f'}
            _fields_ = [('f', dt.String())]
        class U(object):
            _fields_ = {'a': dt.Int64(),
                        'b': dt.Symbol(),
                        'c': dt.Struct(S),
                        'd': dt.List(dt.Int64())}
            _catch_all_ = 'b'
            _tag = None
            def __init__(self, tag, value=None):
                self._tag = tag
                setattr(self, '_' + tag, value)
            def get_a(self):
                return self._a
            def get_c(self):
                return self._c
            def get_d(self):
                return self._d
        U.b = U('b')

        # Test primitive variant
        u = json_decode(dt.Union(U), json.dumps({'a': 64}))
        self.assertEqual(u.get_a(), 64)

        # Test symbol variant
        u = json_decode(dt.Union(U), json.dumps('b'))
        self.assertEqual(u._tag, 'b')
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.Union(U), json.dumps([1,2])))

        # Test struct variant
        u = json_decode(dt.Union(U), json.dumps({'c': {'f': 'hello'}}))
        self.assertEqual(u.get_c().f, 'hello')
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.Union(U), json.dumps({'c': [1,2,3]})))

        # Test list variant
        l = [1, 2, 3, 4]
        u = json_decode(dt.Union(U), json.dumps({'d': l}))
        self.assertEqual(u.get_d(), l)

        # Raises if unknown tag
        self.assertRaises(dt.ValidationError, lambda: json_decode(dt.Union(U), json.dumps('z')))

        # Unknown variant (strict=True)
        self.assertRaises(dt.ValidationError,
                          lambda: json_decode(dt.Union(U), json.dumps({'e': 'test'})))


        # Test catch all variant
        u = json_decode(dt.Union(U), json.dumps({'e': 'test'}), strict=False)
        self.assertEqual(u._tag, 'b')
