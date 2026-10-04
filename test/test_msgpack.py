import msgpack
import pytest

from stone.backends.python_rsrc import stone_serializers as ss
from stone.backends.python_rsrc import stone_validators as bv


@pytest.mark.parametrize('validator,value', [
    (bv.String(), 'hello \u2650'),
    (bv.Bytes(), b'\x00\xff\x80hello'),
    (bv.List(bv.Bytes()), [b'\xff', b'hello', b'']),
    (bv.Map(bv.String(), bv.Bytes()), {'data': b'\xff\x80'}),
])
def test_msgpack_round_trip(validator, value):
    encoded = ss.msgpack_encode(validator, value)
    assert ss.msgpack_decode(validator, encoded) == value


@pytest.mark.parametrize('value', [b'', b'hello', b'\xff\x80\x00hello'])
def test_msgpack_legacy_raw_bytes(value):
    encoded = msgpack.packb(value, use_bin_type=False)
    assert ss.msgpack_decode(bv.Bytes(), encoded) == value


def test_msgpack_alias_validators():
    validator = bv.String()
    calls = []

    def reject(value):
        calls.append(value)
        raise bv.ValidationError('alias rejected')

    with pytest.raises(bv.ValidationError, match='alias rejected'):
        ss.msgpack_decode(
            validator, msgpack.packb('hello'), alias_validators={validator: reject})
    assert calls == ['hello']


def test_msgpack_strict_option():
    encoded = msgpack.packb('unexpected')
    with pytest.raises(bv.ValidationError, match='expected null'):
        ss.msgpack_decode(bv.Void(), encoded)
    assert ss.msgpack_decode(bv.Void(), encoded, strict=False) is None
