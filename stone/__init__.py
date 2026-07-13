try:
    from ._version import __version__
except ModuleNotFoundError:
    # A source tree that has not been built or installed yet.
    __version__ = '0.0.0.dev0'

__all__ = ('__version__',)
