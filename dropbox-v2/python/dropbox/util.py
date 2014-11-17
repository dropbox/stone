def assert_only_one(**kwargs):
    """Raises an error if more or less than one key in kwargs has a non-None
    value."""
    set_key = None
    for k, v in kwargs.items():
        if v is not None:
            assert set_key is None, (
                'Only either {!r} or {!r} should be set'.format(set_key, k)
            )
            set_key = k
    assert set_key is not None, 'One key must be set'
    return set_key
