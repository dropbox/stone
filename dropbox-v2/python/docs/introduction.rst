************
Introduction
************

This package gives you an interface to the Dropbox Core API (v2).

Quick Start
===========

To get started, you should instantiate the :class:`dropbox.Dropbox` class.
You'll need an OAuth 2 token for a user. The easiest way to obtain one is
to go to the `Developer Console for your app <https://www.dropbox.com/developers/apps>`_
and use the "Generate Access Token" button to create one for your personal
account.

.. code-block:: python

    >>> from dropbox import Dropbox
    >>> dbx = Dropbox(OAUTH2_TOKEN)

Using ``dbx`` you can query information for your account using :func:`~dropbox.base_users.BaseUsers.info_me`

.. code-block:: python

    >>> account = dbx.users.info_me()
    >>> print account.me.name.display_name
    "John"
    >>> print account.me.account_id
    'dbid:AAH4f99T0taONIb-OurWxbNQ6ywzRopQngc'

To see a list of all the attributes available, see :class:`~dropbox.base_users.AccountInfo`.

Namespaces
==========

The Dropbox API is divided into namespaces that group similar functionality
together. Namespaces are accessible as attribues of the :class:`dropbox.Dropbox`
class. For example, the :class:`~dropbox.files.Files` and
:class:`~dropbox.base_users.BaseUsers` namespaces map to ``dbx.files`` and
``dbx.users``.

Tagged Unions
=============

The Dropbox API makes use of tagged unions to represent certain data types.
Whereas a struct is made up of fields, each with an associated value, a tagged
union guarantees that of all the possible fields, only one is specified.

An example of this is the :class:`dropbox.base_users.AccountInfo` union, which
is returned when calling the :meth:`dropbox.base_users.BaseUsers.info` method.
Only one of its three possible member fields, ``me``, ``teammate``, or ``user``
will ever be populated at one time. You can handle each case by writing code
like the following:

.. code-block:: python

    ai = dbx.users.info(ACCOUNT_ID)
    if ai.is_me():
        print 'This account is me', ai.me
    elif ai.is_teammate():
        print 'This account is a teammate', ai.teammate
    elif ai.is_user():
        print 'This account is some other user', ai.user

In certain cases, you may need to instantiate a tagged union as an argument to
a function. An example of this is the :meth:`dropbox.base_files.BaseFiles.upload` method.

The method requires you to pass in an instance of :class:`dropbox.files.ConflictPolicy`
for the ``mode`` argument.
