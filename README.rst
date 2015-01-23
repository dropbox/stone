*****
Babel
*****

Define an API once in Babel. Use code generators to translate your
specification into objects and functions in the programming languages
of your choice.

Currently, only Python is supported as a generation target. Swift is being
actively worked on, and the intention is to support
`several other languages <doc/using_generator.rst>`_.

    * Introduction
        * Motivation_
        * Install_
        * `Taste of Babel <taste-of-babel_>`_
    * `Language Reference (.babel) <doc/lang_ref.rst>`_
        * `Choosing a Filename <doc/lang_ref.rst#filename>`_
        * `Comments <doc/lang_ref.rst#comments>`_
        * `Namespace <doc/lang_ref.rst#namespace>`_
        * `Primitive Types <doc/lang_ref.rst#primitive-types>`_
        * `Struct <doc/lang_ref.rst#struct>`_
        * `Union <doc/lang_ref.rst#union>`_
        * `Alias <doc/lang_ref.rst#alias>`_
        * `Route <doc/lang_ref.rst#route>`_
        * `Documentation <doc/lang_ref.rst#documentation>`_
        * `Formal Grammar <doc/lang_ref.rst#formal-grammar>`_
    * `Using a Generator <doc/using_generator.rst>`_
        * `Compile with the CLI <doc/using_generator.rst#compile>`_
        * `Python Generation <doc/using_generator.rst#python-gen>`_
    * `Managing Large Specs <doc/managing_large_specs.rst>`_
        * `Using Namespaces <doc/managing_large_specs.rst#using-namespaces>`_
        * `Splitting a Namespace Across Files <doc/managing_large_specs.rst#splitting-namespace>`_
        * `Using Header Files <doc/managing_large_specs.rst#using-headers>`_
        * `Separating Public and Private Routes <doc/managing_large_specs.rst#public-private>`_
    * `Evolving a Spec <doc/evolve_spec.rst>`_
        * `Background <doc/evolve_spec.rst#background>`_
        * `Sender-Recipient <doc/evolve_spec.rst#sender-recipient>`_
        * `Backwards Incompatible Changes <doc/evolve_spec.rst#backwards-incompat>`_
        * `Backwards Compatible Changes <doc/evolve_spec.rst#backwards-compat>`_
        * `Planning for Backwards Compatibility <doc/evolve_spec.rst#planning-for-compat>`_
        * `Leader-Clients <doc/evolve_spec.rst#leader-clients>`_
        * `Route Versioning <doc/evolve_spec.rst#route-versioning>`_
    * `Generator Reference (.babelg.py) <doc/generator_ref.rst>`_
        * `Using the API Object <doc/generator_ref.rst#api-obj>`_
        * `Creating an Output File <doc/generator_ref.rst#output-file>`_
        * `Emit Methods <doc/generator_ref.rst#emit_methods>`_
        * `Indentation <doc/generator_ref.rst#indentation>`_
        * `Examples <doc/generator_ref.rst#examples>`_
    * `Wire Format <doc/wire_format.rst>`_

.. _motivation:

Motivation
==========

Being an API designer is tough. There are an innumerable number of protocols
and serialization formats that two hosts can use to communicate. Today, JSON
over HTTP is gaining popularity, but just a few years ago, XML was the
standard. To compound the issue, developers need to support an increasing
number of language-specific SDKs to gain wide adoption.

Babel seeks to:

    1. Define API endpoints in terms of input and output data types that can
       be consistently implemented in different protocols and languages.
    2. Offer structs (product types) and tagged unions (sum types) as fundamental
       data types for modeling APIs flexibly, but strictly.
    3. Improve the visibility developers have into their APIs by centralizing
       specification and documentation.

If we only had one protocol and one language Babel API wouldn't be needed, but
unfortunately humanity was handicapped for good reason. See
`Why do we have multiple programming languages?`_

Assumptions
-----------

Babel makes no assumptions about the protocol layer being used to make API
requests and return responses; its first use case is the Dropbox v2 API which
operates over HTTP. Babel does not come with nor enforce any particular RPC
framework.

Babel makes some assumptions about the data types supported in the serialization
format and target programming language. It's assumed that there is a capacity
for representing dictionaries (unordered string keys -> value), lists, numeric
types, and strings. The intention is for Babel to map to a multitude of
serialization formats from JSON to more space-efficient representations.

Babel assumes that a route (or API endpoint) can have its request and
response types defined without relation to each other. In other words, the
type of response does not change based on the input to the endpoint. An
exception to this rule is afforded for error responses.

.. _install:

Installation
============

Download or clone BabelAPI, and run the following in its root directory::

   $ sudo python setup.py install

This will install a script ``babelapi`` to your PATH that can be run from the
command line::

   $ babelapi -h

If you did not run ``setup.py`` but have the Python package in your PYTHONPATH,
you can replace ``babelapi`` with ``python -m babelapi.cli`` as follows::

   $ python -m babelapi.cli -h

.. _taste-of-babel:

A Taste of Babel
================

Here we define a hypothetical route that shows up in some form or another in
APIs for web services: querying the account information for a user of a
service. Our hypothetical spec lives in a file called ``users.babel``::

    # We put this in the "users" namespace in anticipation that
    # there would be many user-account-related routes.
    namespace users

    # We define an AccountId as being a 10-character string
    # once here to avoid declaring it each time.
    alias AccountId = String(min_length=10, max_length=10)

    union Status
        active
            "The account is active."
        inactive Timestamp(format="%a, %d %b %Y %H:%M:%S")
            "The account is inactive. The value is when the account was
            deactivated."

    struct Account
        "Information about a user's account."

        account_id AccountId
            "A unique identifier for the user's account."
        email String(pattern="^[^@]+@[^@]+\.[^@]+$")
            "The e-mail address of the user."
        name String(min_length=1)?
            "The user's full name. :val:`null` if no name was provided."
        status Status
            "The status of the account."

        example default "A regular user"
            account_id="id-48sa2f0"
            email="alex@example.org"
            name="Alexander the Great"

    # This struct represents the input data to the route.
    struct GetAccountReq
        account_id AccountId

    # This union represents the possible errors that might be returned.
    union GetAccountErr
        no_account
            "No account with the requested id could be found."
        perm_denied Any
            "Insufficient privileges to query account information."
        unknown*

    route get_account (GetAccountReq, Account, GetAccountErr)
        "Get information about a specified user's account."

Using the Python generator, we can generate a Python module that mirrors this
specification using the command-line interface::

    $ babelapi python users.babel .
    INFO:babelapi.idl:Parsing spec users.babel
    INFO:babelapi.compiler:Found generator at ...
    INFO:babelapi.compiler:Running generator ...
    INFO:bablesdk.generator.PythonGenerator:Copying babel_data_types.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Copying babel_serializers.py to output folder
    INFO:bablesdk.generator.PythonGenerator:Generating ./users.py

Now we can interact with the specification in Python::

    $ python -i users.py
    >>> a = Account()
    >>> a.account_id = 1234 # fails type validation
    Traceback (most recent call last):
      ...
    babel_data_types.ValidationError: '1234' expected to be a string, got integer

    >>> a.account_id = '1234' # fails length validation
    Traceback (most recent call last):
      ...
    babel_data_types.ValidationError: '1234' must be at least 10 characters, got 4

    >>> a.account_id = 'id-48sa2f0' # passes validation

    >>> # Now we use the included JSON serializer
    >>> from babel_serializers import json_encode
    >>> a2 = Account(account_id='id-48sa2f0', name='Alexander the Great',
    ...              email='alex@example.org', status=Status.active)
    >>> json_encode(GetAccountRoute.response_data_type, a2)
    '{"status": "active", "account_id": "id-48sa2f0", "name": "Alexander the Great", "email": "alex@example.org"}'

.. _why_multiple_languages:

Why do we have multiple programming languages?
==============================================

From the King James version of the Bible:

    4 And they said, Go to, let us build us a city and a tower, whose top may reach unto heaven; and let us make us a name, lest we be scattered abroad upon the face of the whole earth.

    5 And the Lord came down to see the city and the tower, which the children of men builded.

    6 And the Lord said, Behold, the people is one, and they have all one language; and this they begin to do: and now nothing will be restrained from them, which they have imagined to do.

    7 Go to, let us go down, and there confound their language, that they may not understand one another's speech.

    8 So the Lord scattered them abroad from thence upon the face of all the earth: and they left off to build the city.

    9 Therefore is the name of it called Babel; because the Lord did there confound the language of all the earth: and from thence did the Lord scatter them abroad upon the face of all the earth.

    —Genesis 11:4–9[1]
