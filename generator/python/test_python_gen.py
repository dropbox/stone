from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import datetime
import imp
import json
import os
import shutil
import six
import subprocess
import sys
import unittest

import babel_validators as bv

from babel_serializers import (
    json_compat_obj_encode,
    json_compat_obj_decode,
    json_encode,
    json_decode,
)


class TestDropInModules(unittest.TestCase):
    """
    Tests the babel_serializers and babel_validators modules.
    """

    def mk_validator_testers(self, validator):
        def p(i):
            validator.validate(i)
        def f(i):
            self.assertRaises(bv.ValidationError, validator.validate, i)
        return p, f  # 'p(input)' if you expect it to pass, 'f(input)' if you expect it to fail.

    def test_string_validator(self):
        s = bv.String(min_length=1, max_length=5, pattern='[A-z]+')
        # Not a string
        self.assertRaises(bv.ValidationError, lambda: s.validate(1))
        # Too short
        self.assertRaises(bv.ValidationError, lambda: s.validate(''))
        # Too long
        self.assertRaises(bv.ValidationError, lambda: s.validate('a'*6))
        # Doesn't pass regex
        self.assertRaises(bv.ValidationError, lambda: s.validate('#'))
        # Passes
        s.validate('a')
        # Check that the validator is converting all strings to unicode
        self.assertEqual(type(s.validate('a')), six.text_type)

    def test_string_regex_anchoring(self):
        p, f = self.mk_validator_testers(bv.String(pattern=r'abc|xyz'))
        p('abc')
        p('xyz')
        f('_abc')
        f('abc_')
        f('_xyz')
        f('xyz_')

    def test_boolean_validator(self):
        b = bv.Boolean()
        b.validate(True)
        b.validate(False)
        self.assertRaises(bv.ValidationError, lambda: b.validate(1))

    def test_integer_validator(self):
        i = bv.UInt32(min_value=10, max_value=100)
        # Not an integer
        self.assertRaises(bv.ValidationError, lambda: i.validate(1.4))
        # Too small
        self.assertRaises(bv.ValidationError, lambda: i.validate(1))
        # Too large
        self.assertRaises(bv.ValidationError, lambda: i.validate(101))
        # Passes
        i.validate(50)

        # min_value is less than the default for the type
        self.assertRaises(AssertionError, lambda: bv.UInt32(min_value=-3))
        # non-sensical min_value
        self.assertRaises(AssertionError, lambda: bv.UInt32(min_value=1.3))

    def test_float_validator(self):
        f64 = bv.Float64()
        # Too large for a float to represent
        self.assertRaises(bv.ValidationError, lambda: f64.validate(10**310))
        # inf and nan should be rejected
        self.assertRaises(bv.ValidationError, lambda: f64.validate(float('nan')))
        self.assertRaises(bv.ValidationError, lambda: f64.validate(float('inf')))
        # Passes
        f64.validate(1.1 * 10**300)

        # Test a float64 with an additional bound
        f64b = bv.Float64(min_value=0, max_value=100)
        # Check bounds
        self.assertRaises(bv.ValidationError, lambda: f64b.validate(1000))
        self.assertRaises(bv.ValidationError, lambda: f64b.validate(-1))

        # Test a float64 with an invalid bound
        self.assertRaises(AssertionError, lambda: bv.Float64(min_value=0, max_value=10**330))

        f32 = bv.Float32()
        self.assertRaises(bv.ValidationError, lambda: f32.validate(3.5 * 10**38))
        self.assertRaises(bv.ValidationError, lambda: f32.validate(-3.5 * 10**38))
        # Passes
        f32.validate(0)

    def test_bytes_validator(self):
        b = bv.Bytes(min_length=1, max_length=10)
        # Not a valid binary type
        self.assertRaises(bv.ValidationError, lambda: b.validate(u'asdf'))
        # Too short
        self.assertRaises(bv.ValidationError, lambda: b.validate(b''))
        # Too long
        self.assertRaises(bv.ValidationError, lambda: b.validate(b'\x00'*11))
        # Passes
        b.validate(b'\x00')

    def test_timestamp_validator(self):
        class UTC(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)
            def tzname(self, dt):
                return 'UTC'
            def dst(self, dt):
                return datetime.timedelta(0)
        class PST(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(-8)
            def tzname(self, dt):
                return 'PST'
            def dst(self, dt):
                return datetime.timedelta(0)
        t = bv.Timestamp('%a, %d %b %Y %H:%M:%S +0000')
        self.assertRaises(bv.ValidationError, lambda: t.validate('abcd'))
        now = datetime.datetime.utcnow()
        t.validate(now)
        # Accept a tzinfo only if it's UTC
        t.validate(now.replace(tzinfo=UTC()))
        # Do not accept a non-UTC tzinfo
        self.assertRaises(bv.ValidationError,
                          lambda: t.validate(now.replace(tzinfo=PST())))

    def test_list_validator(self):
        l = bv.List(bv.String(), min_items=1, max_items=10)
        # Not a valid list type
        self.assertRaises(bv.ValidationError, lambda: l.validate('a'))
        # Too short
        self.assertRaises(bv.ValidationError, lambda: l.validate([]))
        # Too long
        self.assertRaises(bv.ValidationError, lambda: l.validate([1]*11))
        # Not a valid string type
        self.assertRaises(bv.ValidationError, lambda: l.validate([1]))
        # Passes
        l.validate(['a'])

    def test_nullable_validator(self):
        n = bv.Nullable(bv.String())
        # Absent case
        n.validate(None)
        # Fails string validation
        self.assertRaises(bv.ValidationError, lambda: n.validate(123))
        # Passes
        n.validate('abc')
        # Stacking nullables isn't supported by our JSON wire format
        self.assertRaises(AssertionError,
                          lambda: bv.Nullable(bv.Nullable(bv.String())))
        self.assertRaises(AssertionError,
                          lambda: bv.Nullable(bv.Void()))

    def test_void_validator(self):
        v = bv.Void()
        # Passes: Only case that validates
        v.validate(None)
        # Fails validation
        self.assertRaises(bv.ValidationError, lambda: v.validate(123))

    def test_struct_validator(self):
        class C(object):
            _all_field_names_ = {'f'}
            _all_fields_ = [('f', bv.String())]
            f = None
        s = bv.Struct(C)
        self.assertRaises(bv.ValidationError, lambda: s.validate(object()))

    def test_json_encoder(self):
        self.assertEqual(json_encode(bv.Void(), None), json.dumps(None))
        self.assertEqual(json_encode(bv.String(), 'abc'), json.dumps('abc'))
        self.assertEqual(json_encode(bv.String(), u'\u2650'), json.dumps(u'\u2650'))
        self.assertEqual(json_encode(bv.UInt32(), 123), json.dumps(123))
        # Because a bool is a subclass of an int, ensure they aren't mistakenly
        # encoded as a true/false in JSON when an integer is the data type.
        self.assertEqual(json_encode(bv.UInt32(), True), json.dumps(1))
        self.assertEqual(json_encode(bv.Boolean(), True), json.dumps(True))
        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow()
        self.assertEqual(json_encode(bv.Timestamp('%a, %d %b %Y %H:%M:%S +0000'), now),
                         json.dumps(now.strftime(f)))
        b = b'\xff' * 5
        self.assertEqual(json_encode(bv.Bytes(), b),
                         json.dumps(base64.b64encode(b).decode('ascii')))
        self.assertEqual(json_encode(bv.Nullable(bv.String()), None), json.dumps(None))
        self.assertEqual(json_encode(bv.Nullable(bv.String()), u'abc'), json.dumps('abc'))

    def test_json_encoder_union(self):
        class S(object):
            _all_field_names_ = {'f'}
            _all_fields_ = [('f', bv.String())]
        class U(object):
            _tagmap = {'a': bv.Int64(),
                       'b': bv.Void(),
                       'c': bv.Struct(S),
                       'd': bv.List(bv.Int64()),
                       'e': bv.Nullable(bv.Int64()),
                       'f': bv.Nullable(bv.Struct(S))}
            _tag = None
            def __init__(self, tag, value=None):
                self._tag = tag
                self._value = value
            def get_a(self):
                return self._a
            def get_c(self):
                return self._c
            def get_d(self):
                return self._d

        U.b = U('b')

        # Test primitive variant
        u = U('a', 64)
        self.assertEqual(json_encode(bv.Union(U), u, old_style=True),
                         json.dumps({'a': 64}))

        # Test symbol variant
        u = U('b')
        self.assertEqual(json_encode(bv.Union(U), u, old_style=True),
                         json.dumps('b'))

        # Test struct variant
        c = S()
        c.f = 'hello'
        c._f_present = True
        u = U('c', c)
        self.assertEqual(json_encode(bv.Union(U), u, old_style=True),
                         json.dumps({'c': {'f': 'hello'}}))

        # Test list variant
        u = U('d', [1, 2, 3, 'a'])
        # lists should be re-validated during serialization
        self.assertRaises(bv.ValidationError, lambda: json_encode(bv.Union(U), u))
        l = [1, 2, 3, 4]
        u = U('d', [1, 2, 3, 4])
        self.assertEqual(json_encode(bv.Union(U), u, old_style=True),
                         json.dumps({'d': l}))

        # Test a nullable union
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), None),
                         json.dumps(None))
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), u, old_style=True),
                         json.dumps({'d': l}))

        # Test nullable primitive variant
        u = U('e', None)
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), u, old_style=True),
                         json.dumps('e'))
        u = U('e', 64)
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), u, old_style=True),
                         json.dumps({'e': 64}))

        # Test nullable composite variant
        u = U('f', None)
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), u, old_style=True),
                         json.dumps('f'))
        u = U('f', c)
        self.assertEqual(json_encode(bv.Nullable(bv.Union(U)), u, old_style=True),
                         json.dumps({'f': {'f': 'hello'}}))

    def test_json_encoder_error_messages(self):
        class S3(object):
            _all_field_names_ = {'j'}
            _all_fields_ = [('j', bv.UInt64(max_value=10))]
        class S2(object):
            _all_field_names_ = {'i'}
            _all_fields_ = [('i', bv.Struct(S3))]
        class S(object):
            _all_field_names_ = {'f'}
            _all_fields_ = [('f', bv.Struct(S2))]
        class U(object):
            _tagmap = {'t': bv.Nullable(bv.Struct(S))}
            _tag = None
            _catch_all = None
            def __init__(self, tag, value=None):
                self._tag = tag
                self._value = value
            def get_t(self):
                return self._t

        s = S()
        s.f = S2()
        s._f_present = True
        s.f.i = S3()
        s.f._i_present = True
        s.f.i._j_present = False

        # Test that validation error references outer and inner struct
        with self.assertRaises(bv.ValidationError):
            try:
                json_encode(bv.Struct(S), s)
            except bv.ValidationError as e:
                prefix = 'f.i: '
                self.assertEqual(prefix, str(e)[:len(prefix)])
                raise

        u = U('t', s)

        # Test that validation error references outer union and inner structs
        with self.assertRaises(bv.ValidationError):
            try:
                json_encode(bv.Union(U), u)
            except bv.ValidationError as e:
                prefix = 't.f.i: '
                self.assertEqual(prefix, str(e)[:len(prefix)])
                raise

    def test_json_decoder(self):
        self.assertEqual(json_decode(bv.String(), json.dumps('abc')), 'abc')
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.String(), json.dumps(32)))

        self.assertEqual(json_decode(bv.UInt32(), json.dumps(123)), 123)
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.UInt32(), json.dumps('hello')))

        self.assertEqual(json_decode(bv.Boolean(), json.dumps(True)), True)
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Boolean(), json.dumps(1)))

        f = '%a, %d %b %Y %H:%M:%S +0000'
        now = datetime.datetime.utcnow().replace(microsecond=0)
        self.assertEqual(json_decode(bv.Timestamp('%a, %d %b %Y %H:%M:%S +0000'),
                                     json.dumps(now.strftime(f))),
                         now)
        b = b'\xff' * 5
        self.assertEqual(json_decode(bv.Bytes(),
                                     json.dumps(base64.b64encode(b).decode('ascii'))),
                         b)
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Bytes(), json.dumps(1)))
        self.assertEqual(json_decode(bv.Nullable(bv.String()), json.dumps(None)), None)
        self.assertEqual(json_decode(bv.Nullable(bv.String()), json.dumps('abc')), 'abc')

        self.assertEqual(json_decode(bv.Void(), json.dumps(None)), None)
        # Check that void can take any input if strict is False.
        self.assertEqual(json_decode(bv.Void(), json.dumps(12345), strict=False), None)
        # Check that an error is raised if strict is True and there's a non-null value
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Void(), json.dumps(12345), strict=True))

    def test_json_decoder_struct(self):
        class S(object):
            _all_field_names_ = {'f', 'g'}
            _all_fields_ = [('f', bv.String()),
                            ('g', bv.Nullable(bv.String()))]
            _g = None
            @property
            def f(self):
                return self._f
            @f.setter
            def f(self, val):
                self._f = val
            @property
            def g(self):
                return self._g
            @g.setter
            def g(self, val):
                self._g = val

        # Required struct fields must be present
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Struct(S), json.dumps({})))
        json_decode(bv.Struct(S), json.dumps({'f': 't'}))

        # Struct fields can have null values for nullable fields
        msg = json.dumps({'f': 't', 'g': None})
        json_decode(bv.Struct(S), msg)

        # Unknown struct fields raise error if strict
        msg = json.dumps({'f': 't', 'z': 123})
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Struct(S), msg, strict=True))
        json_decode(bv.Struct(S), msg, strict=False)

    def test_json_decoder_union(self):
        class S(object):
            _all_field_names_ = {'f'}
            _all_fields_ = [('f', bv.String())]
        class U(object):
            _tagmap = {'a': bv.Int64(),
                       'b': bv.Void(),
                       'c': bv.Struct(S),
                       'd': bv.List(bv.Int64()),
                       'e': bv.Nullable(bv.Int64()),
                       'f': bv.Nullable(bv.Struct(S))}
            _catch_all = 'b'
            _tag = None
            def __init__(self, tag, value=None):
                self._tag = tag
                self._value = value
            def get_a(self):
                return self._value
            def get_c(self):
                return self._value
            def get_d(self):
                return self._value
        U.b = U('b')

        # Test primitive variant
        u = json_decode(bv.Union(U), json.dumps({'a': 64}), old_style=True)
        self.assertEqual(u.get_a(), 64)

        # Test void variant
        u = json_decode(bv.Union(U), json.dumps('b'))
        self.assertEqual(u._tag, 'b')
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Union(U), json.dumps({'b': [1,2]})))
        u = json_decode(bv.Union(U), json.dumps({'b': [1,2]}), strict=False, old_style=True)
        self.assertEqual(u._tag, 'b')

        # Test struct variant
        u = json_decode(bv.Union(U), json.dumps({'c': {'f': 'hello'}}), old_style=True)
        self.assertEqual(u.get_c().f, 'hello')
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Union(U), json.dumps({'c': [1,2,3]})))

        # Test list variant
        l = [1, 2, 3, 4]
        u = json_decode(bv.Union(U), json.dumps({'d': l}), old_style=True)
        self.assertEqual(u.get_d(), l)

        # Raises if unknown tag
        self.assertRaises(bv.ValidationError, lambda: json_decode(bv.Union(U), json.dumps('z')))

        # Unknown variant (strict=True)
        self.assertRaises(bv.ValidationError,
                          lambda: json_decode(bv.Union(U), json.dumps({'z': 'test'})))

        # Test catch all variant
        u = json_decode(bv.Union(U), json.dumps({'z': 'test'}),
                        strict=False, old_style=True)
        self.assertEqual(u._tag, 'b')

        # Test nullable union
        u = json_decode(bv.Nullable(bv.Union(U)), json.dumps(None),
                        strict=False, old_style=True)
        self.assertEqual(u, None)

        # Test nullable union member
        u = json_decode(bv.Union(U), json.dumps('e'))
        self.assertEqual(u._tag, 'e')
        self.assertEqual(u._value, None)
        u = json_decode(bv.Union(U), json.dumps({'e': 64}),
                        strict=False, old_style=True)
        self.assertEqual(u._tag, 'e')
        self.assertEqual(u._value, 64)

        # Test nullable composite variant
        u = json_decode(bv.Union(U), json.dumps('f'))
        self.assertEqual(u._tag, 'f')
        u = json_decode(bv.Union(U), json.dumps({'f': {'f': 'hello'}}),
                        strict=False, old_style=True)
        self.assertEqual(type(u._value), S)
        self.assertEqual(u._value.f, 'hello')

    def test_json_decoder_error_messages(self):
        class S3(object):
            _all_field_names_ = {'j'}
            _all_fields_ = [('j', bv.UInt64(max_value=10))]
        class S2(object):
            _all_field_names_ = {'i'}
            _all_fields_ = [('i', bv.Struct(S3))]
        class S(object):
            _all_field_names_ = {'f'}
            _all_fields_ = [('f', bv.Struct(S2))]
        class U(object):
            _tagmap = {'t': bv.Nullable(bv.Struct(S))}
            _tag = None
            _catch_all = None
            def __init__(self, tag, value=None):
                self._tag = tag
                self._value = value
            def get_t(self):
                return self._value

        # Test that validation error references outer and inner struct
        with self.assertRaises(bv.ValidationError):
            try:
                json_decode(bv.Struct(S), json.dumps({'f': {'i': {}}}), strict=False)
            except bv.ValidationError as e:
                prefix = 'f.i: '
                self.assertEqual(prefix, str(e)[:len(prefix)])
                raise

        # Test that validation error references outer union and inner structs
        with self.assertRaises(bv.ValidationError):
            try:
                json_decode(bv.Union(U), json.dumps({'t': {'f': {'i': {}}}}),
                            strict=False, old_style=True)
            except bv.ValidationError as e:
                prefix = 't.f.i: '
                self.assertEqual(prefix, str(e)[:len(prefix)])
                raise


test_spec = """\
namespace ns

import ns2

struct A
    "Sample struct doc."
    a String
        "Sample field doc."
    b Int64

struct B extends A
    c Bytes

struct C extends B
    d Float64

struct D
    a String
    b UInt64 = 10
    c String?
    d List(Int64?)

struct E
    a String = "test"
    b UInt64 = 10
    c Int64?

struct DocTest
    b Boolean
        "If :val:`true` then..."
    t String
        "References :type:`D`."

union U
    "Sample union doc."
    t0
        "Sample field doc."
    t1 String

union V
    t0
    t1 String
    t2 String?
    t3 S
    t4 S?
    t5 U
    t6 U?
    t7 Resource
    t8 Resource?
    t9 List(String)
    t10 List(U)

struct S
    f String

struct Resource
    union
        file File
        folder Folder

    name String

struct File extends Resource
    size UInt64

struct Folder extends Resource
    "Regular folder"

# Differs from Resource because it's a catch-all
struct ResourceLax
    union*
        file File2
        folder Folder2

    name String

struct File2 extends ResourceLax
    size UInt64

struct Folder2 extends ResourceLax
    "Regular folder"

struct ImportTestS extends ns2.BaseS
    a String

union ImportTestU extends ns2.BaseU
    a UInt64
"""

test_ns2_spec = """\
namespace ns2

struct BaseS
    z Int64

union BaseU
    z
    x String
"""

class TestGeneratedPython(unittest.TestCase):

    def setUp(self):

        # Sanity check: babelapi must be importable for the compiler to work
        __import__('babelapi')

        # Write spec to file for babelapi
        with open('ns.babel', 'w') as f:
            f.write(test_spec)
        with open('ns2.babel', 'w') as f:
            f.write(test_ns2_spec)

        # Compile spec by calling out to babelapi
        p = subprocess.Popen(
            [sys.executable,
             '-m',
             'babelapi.cli',
             'python.babelg.py',
             'ns.babel',
             'ns2.babel',
             'output/'],
            stderr=subprocess.PIPE)
        if p.wait() != 0:
            raise AssertionError('Could not execute babelapi tool: %s' %
                                 p.stderr.read().decode('ascii'))

        # Load ns2 first since ns depends on it.
        self.ns2 = imp.load_source('ns2', 'output/ns2.py')
        self.ns = imp.load_source('ns', 'output/ns.py')

    def test_docstring(self):
        # Check that the docstrings from the spec have in some form made it
        # into the Python docstrings for the generated objects.
        self.assertIn('Sample struct doc.', self.ns.A.__doc__)
        self.assertIn('Sample field doc.', self.ns.A.a.__doc__)
        self.assertIn('Sample union doc.', self.ns.U.__doc__)
        self.assertIn('Sample field doc.', self.ns.U.t0.__doc__)

        # Test doc conversion of Python bool.
        self.assertIn('``True``', self.ns.DocTest.b.__doc__)
        # Test doc converts type reference to sphinx-friendly representation.
        self.assertIn(':class:`D`', self.ns.DocTest.t.__doc__)

    def test_struct_decoding(self):
        d = json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'b': 1, 'c': 'C', 'd': []}))
        self.assertIsInstance(d, self.ns.D)
        self.assertEqual(d.a, 'A')
        self.assertEqual(d.b, 1)
        self.assertEqual(d.c, 'C')
        self.assertEqual(d.d, [])

        # Test with missing value for nullable field
        d = json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'b': 1, 'd': []}))
        self.assertEqual(d.a, 'A')
        self.assertEqual(d.b, 1)
        self.assertEqual(d.c, None)
        self.assertEqual(d.d, [])

        # Test with missing value for field with default
        d = json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'c': 'C', 'd': [1]}))
        self.assertEqual(d.a, 'A')
        self.assertEqual(d.b, 10)
        self.assertEqual(d.c, 'C')
        self.assertEqual(d.d, [1])

        # Test with explicitly null value for nullable field
        d = json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'c': None, 'd': [1, 2]}))
        self.assertEqual(d.a, 'A')
        self.assertEqual(d.c, None)
        self.assertEqual(d.d, [1, 2])

        # Test with None and numbers in list
        d = json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'c': None, 'd': [None, 1]}))
        self.assertEqual(d.a, 'A')
        self.assertEqual(d.c, None)
        self.assertEqual(d.d, [None, 1])

        # Test with explicitly null value for field with default
        with self.assertRaises(bv.ValidationError) as cm:
            json_decode(bv.Struct(self.ns.D),
                        json.dumps({'a': 'A', 'b': None}))
        self.assertEqual("b: expected integer, got null", str(cm.exception))

    def test_union_decoding_old(self):
        v = json_decode(bv.Union(self.ns.V), json.dumps('t0'))
        self.assertIsInstance(v, self.ns.V)

        # Test verbose representation of a void union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'t0': None}), old_style=True)
        self.assertIsInstance(v, self.ns.V)

        # Test bad value for void union member
        with self.assertRaises(bv.ValidationError) as cm:
            json_decode(bv.Union(self.ns.V), json.dumps({'t0': 10}), old_style=True)
        self.assertEqual("expected null, got integer", str(cm.exception))

        # Test compact representation of a nullable union member with missing value
        v = json_decode(bv.Union(self.ns.V), json.dumps('t2'))
        self.assertIsInstance(v, self.ns.V)

        # Test verbose representation of a nullable union member with missing value
        v = json_decode(bv.Union(self.ns.V), json.dumps({'t2': None}), old_style=True)
        self.assertIsInstance(v, self.ns.V)

        # Test verbose representation of a nullable union member with bad value
        with self.assertRaises(bv.ValidationError) as cm:
            json_decode(bv.Union(self.ns.V), json.dumps({'t2': 123}), old_style=True)
        self.assertEqual("'123' expected to be a string, got integer", str(cm.exception))

    def test_union_decoding(self):
        v = json_decode(bv.Union(self.ns.V), json.dumps('t0'))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t0())

        # Test verbose representation of a void union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't0'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t0())

        # Test extra verbose representation of a void union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't0', 't0': None}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t0())

        # Test error: extra key
        with self.assertRaises(bv.ValidationError) as cm:
            v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't0', 'unk': 123}))
        self.assertEqual("unexpected key 'unk'", str(cm.exception))

        # Test error: bad type
        with self.assertRaises(bv.ValidationError) as cm:
            v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 123}))
        self.assertEqual('tag must be string, got integer', str(cm.exception))

        # Test primitive union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't1', 't1': 'hello'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t1())
        self.assertEqual(v.get_t1(), 'hello')

        # Test nullable primitive union member with null value
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't2', 't2': None}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t2())
        self.assertEqual(v.get_t2(), None)

        # Test nullable primitive union member that is missing
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't2'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t2())
        self.assertEqual(v.get_t2(), None)

        # Test error: extra key
        with self.assertRaises(bv.ValidationError) as cm:
            json_decode(bv.Union(self.ns.V),
                        json.dumps({'.tag': 't2', 't2': None, 'unk': 123}))
        self.assertEqual("unexpected key 'unk'", str(cm.exception))

        # Test composite union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't3', 'f': 'hello'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t3())
        self.assertIsInstance(v.get_t3(), self.ns.S)
        self.assertEqual(v.get_t3().f, 'hello')

        # Test error: extra key
        with self.assertRaises(bv.ValidationError) as cm:
            json_decode(bv.Union(self.ns.V),
                        json.dumps({'.tag': 't3', 'f': 'hello', 'g': 'blah'}))
        self.assertEqual("t3: unknown field 'g'", str(cm.exception))

        # Test composite union member with unknown key, but strict is False
        v = json_decode(bv.Union(self.ns.V),
                        json.dumps({'.tag': 't3', 'f': 'hello', 'g': 'blah'}),
                        strict=False)
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t3())
        self.assertIsInstance(v.get_t3(), self.ns.S)
        self.assertEqual(v.get_t3().f, 'hello')

        # Test nullable composite union member
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't4', 'f': 'hello'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t4())
        self.assertIsInstance(v.get_t4(), self.ns.S)
        self.assertEqual(v.get_t4().f, 'hello')

        # Test nullable composite union member that's null
        v = json_decode(bv.Union(self.ns.V), json.dumps({'.tag': 't4'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t4())
        self.assertIsNone(v.get_t4())

        # Test stacked unions
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't5', 't5': {'.tag': 't1', 't1': 'hello'}}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t5(), None)
        self.assertIsInstance(v.get_t5(), self.ns.U)
        u = v.get_t5()
        self.assertEqual(u.get_t1(), 'hello')

        # Test stacked unions with null
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't6'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertTrue(v.is_t6(), None)
        self.assertEqual(v.get_t6(), None)

        # Test member that enumerates subtypes
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't7', 't7': {'.tag': 'file', 'name': 'test', 'size': 1024}}))
        self.assertIsInstance(v, self.ns.V)
        self.assertIsInstance(v.get_t7(), self.ns.File)
        f = v.get_t7()
        self.assertEqual(f.name, 'test')
        self.assertEqual(f.size, 1024)

        # Test member that enumerates subtypes with null
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't8'}))
        self.assertIsInstance(v, self.ns.V)
        self.assertEqual(v.get_t8(), None)

        # Test member that is a list
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't9', 't9': ['a', 'b']}))
        self.assertIsInstance(v, self.ns.V)
        self.assertEqual(v.get_t9(), ['a', 'b'])

        # Test member that is a list of composites
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'.tag': 't10', 't10': [{'.tag': 't1', 't1': 'hello'}]}))
        self.assertIsInstance(v, self.ns.V)
        t10 = v.get_t10()
        self.assertEqual(t10[0].get_t1(), 'hello')

        # Test member that is a list of composites (old style)
        v = json_decode(
            bv.Union(self.ns.V),
            json.dumps({'t10': [{'t1': 'hello'}]}),
            old_style=True)
        self.assertIsInstance(v, self.ns.V)
        t10 = v.get_t10()
        self.assertEqual(t10[0].get_t1(), 'hello')

    def test_union_encoding(self):
        # Test void union member
        v_t0 = self.ns.V.t0
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t0),
                         {'.tag': 't0'})

        # Test that the .tag key comes first
        v = json_compat_obj_encode(bv.Union(self.ns.V), v_t0)
        self.assertEqual(list(v.keys())[0], '.tag')

        # Test primitive union member
        v_t1 = self.ns.V.t1('hello')
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t1),
                         {'.tag': 't1', 't1': 'hello'})

        # Test nullable primitive union member
        v_t2 = self.ns.V.t2('hello')
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t2),
                         {'.tag': 't2', 't2': 'hello'})

        # Test nullable primitive union member that's null
        v_t2 = self.ns.V.t2(None)
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t2),
                         {'.tag': 't2'})

        # Test composite union member
        s = self.ns.S(f='hello')
        v_t3 = self.ns.V.t3(s)
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t3),
                         {'.tag': 't3', 'f': 'hello'})

        # Test nullable composite union member
        s = self.ns.S(f='hello')
        v_t4 = self.ns.V.t4(s)
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t4),
                         {'.tag': 't4', 'f': 'hello'})

        # Test nullable composite union member that's null
        v_t4 = self.ns.V.t4(None)
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t4),
                         {'.tag': 't4'})

        # Test stacked unions
        v_t5 = self.ns.V.t5(self.ns.U.t1('hello'))
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t5),
                         {'.tag': 't5', 't5': {'.tag': 't1', 't1': 'hello'}})

        # Test stacked unions with null
        v_t6 = self.ns.V.t6(None)
        self.assertEqual(json_compat_obj_encode(bv.Union(self.ns.V), v_t6),
                         {'.tag': 't6'})

        # Test member that enumerates subtypes
        v_t7 = self.ns.V.t7(self.ns.File(name='test', size=1024))
        self.assertEqual(
            json_compat_obj_encode(bv.Union(self.ns.V), v_t7),
            {'.tag': 't7', 't7': {'.tag': 'file', 'name': 'test', 'size': 1024}})

        # Test member that enumerates subtypes but is null
        v_t8 = self.ns.V.t8(None)
        self.assertEqual(
            json_compat_obj_encode(bv.Union(self.ns.V), v_t8),
            {'.tag': 't8'})

        # Test member that is a list
        v_t9 = self.ns.V.t9(['a', 'b'])
        self.assertEqual(
            json_compat_obj_encode(bv.Union(self.ns.V), v_t9),
            {'.tag': 't9', 't9': ['a', 'b']})

    def test_list_coding(self):
        # Test decoding list of composites
        v = json_decode(
            bv.List(bv.Struct(self.ns.S)),
            json.dumps([{'f': 'Test'}]))
        self.assertIsInstance(v, list)
        self.assertIsInstance(v[0], self.ns.S)
        self.assertEqual(v[0].f, 'Test')

        # Test encoding list of composites
        v = json_encode(
            bv.List(bv.Struct(self.ns.S)),
            [self.ns.S('Test')])
        self.assertEqual(v, json.dumps([{'f': 'Test'}]))

    def test_objs(self):

        # Test initializing struct params (also tests parent class fields)
        a = self.ns.C(a='test', b=123, c=b'\x00', d=3.14)
        self.assertEqual(a.a, 'test')
        self.assertEqual(a.b, 123)
        self.assertEqual(a.c, b'\x00')
        self.assertEqual(a.d, 3.14)

        # Test that void union member is available as a class attribute
        self.assertIsInstance(self.ns.U.t0, self.ns.U)

        # Test that non-void union member is callable (should be a method)
        self.assertTrue(callable(self.ns.U.t1))

    def test_struct_enumerated_subtypes_encoding(self):
        # Test serializing a leaf struct from  the root struct
        fi = self.ns.File(name='test.doc', size=100)
        self.assertEqual(
            json_compat_obj_encode(bv.StructTree(self.ns.Resource), fi),
            {'.tag': 'file', 'name': 'test.doc', 'size': 100})

        # Test that the .tag key comes first
        v = json_compat_obj_encode(bv.StructTree(self.ns.Resource), fi)
        self.assertEqual(list(v.keys())[0], '.tag')

        # Test serializing a leaf struct as the base and target
        self.assertEqual(
            json_compat_obj_encode(bv.Struct(self.ns.File), fi),
            {'name': 'test.doc', 'size': 100})

    def test_struct_enumerated_subtypes_decoding(self):
        # Test deserializing a leaf struct from  the root struct
        fi = json_compat_obj_decode(
            bv.StructTree(self.ns.Resource),
            {'.tag': 'file', 'name': 'test.doc', 'size': 100})
        self.assertIsInstance(fi, self.ns.File)
        self.assertEqual(fi.name, 'test.doc')
        self.assertEqual(fi.size, 100)

        # Test deserializing leaf struct with unknown type tag
        with self.assertRaises(bv.ValidationError) as cm:
            json_compat_obj_decode(
                bv.StructTree(self.ns.Resource),
                {'.tag': 'unk', 'name': 'test.doc'})
        self.assertEqual("unknown subtype 'unk'", str(cm.exception))

        # Test deserializing leaf struct with bad JSON type for type tag
        with self.assertRaises(bv.ValidationError) as cm:
            json_compat_obj_decode(
                bv.StructTree(self.ns.Resource),
                {'.tag': 123, 'name': 'test.doc'})
        self.assertEqual(".tag: expected string, got integer", str(cm.exception))

        # Test deserializing an unknown leaf in strict mode
        with self.assertRaises(bv.ValidationError) as cm:
            json_compat_obj_decode(
                bv.StructTree(self.ns.Resource),
                {'.tag': 'symlink', 'name': 'test'})
        self.assertEqual("unknown subtype 'symlink'", str(cm.exception))

        # Test deserializing an unknown leaf in non-strict mode
        r = json_compat_obj_decode(
            bv.StructTree(self.ns.ResourceLax),
            {'.tag': 'symlink', 'name': 'test'},
            strict=False)
        self.assertIsInstance(r, self.ns.ResourceLax)
        self.assertEqual(r.name, 'test')

        # Test deserializing an unknown leaf in non-strict mode, but with no
        # catch-all
        with self.assertRaises(bv.ValidationError) as cm:
            json_compat_obj_decode(
                bv.StructTree(self.ns.Resource),
                {'.tag': 'symlink', 'name': 'test'},
                strict=False)
        self.assertEqual(
            "unknown subtype 'symlink' and 'Resource' is not a catch-all",
            str(cm.exception))

    def test_defaults(self):
        # Test void type
        v = bv.Void()
        self.assertTrue(v.has_default())
        self.assertEqual(v.get_default(), None)

        # Test nullable type
        n = bv.Nullable(bv.Struct(self.ns.D))
        self.assertTrue(n.has_default())
        self.assertEqual(n.get_default(), None)

        # Test struct where all fields have defaults
        s = bv.Struct(self.ns.E)
        self.assertTrue(s.has_default())
        s.get_default()

        # Test struct where not all fields have defaults
        s = bv.Struct(self.ns.D)
        self.assertFalse(s.has_default())
        self.assertRaises(AssertionError, s.get_default)

    def tearDown(self):
        # Clear input and output of babelapi tool after all tests.
        shutil.rmtree('output')
        os.remove('ns.babel')
        os.remove('ns2.babel')
