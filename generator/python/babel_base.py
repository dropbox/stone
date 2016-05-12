"""
Helpers for representing Babel data types in Python.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

try:
    from . import babel_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import babel_validators as bv


class Union(object):

    # TODO(kelkabany): Possible optimization is to remove _value if a
    # union is composed of only symbols.
    __slots__ = ['_tag', '_value']

    def __init__(self, tag, value=None):
        assert tag in self._tagmap, 'Invalid tag %r.' % tag
        validator = self._tagmap[tag]
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value
