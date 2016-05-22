*****
Stone
*****

Define an API once in Stone. Use code generators to translate your
specification into objects and functions in the programming languages
of your choice.

Currently, only Python is supported as a generation target. Swift is being
actively worked on, and the intention is to support
`several other languages <doc/using_generator.rst>`_.

    * Introduction
        * Motivation_
        * Installation_
    * `Language Reference (.stone) <doc/lang_ref.rst>`_
        * `Choosing a Filename <doc/lang_ref.rst#choosing-a-filename>`_
        * `Comments <doc/lang_ref.rst#comments>`_
        * `Namespace <doc/lang_ref.rst#ns>`_
        * `Primitive Types <doc/lang_ref.rst#primitive-types>`_
        * `Alias <doc/lang_ref.rst#alias>`_
        * `Struct <doc/lang_ref.rst#struct>`_
        * `Union <doc/lang_ref.rst#union>`_
        * `Nullable Type <doc/lang_ref.rst#nullable-type>`_
        * `Route <doc/lang_ref.rst#route>`_
        * `Include <doc/lang_ref.rst#include>`_
        * `Documentation <doc/lang_ref.rst#doc>`_
        * `Formal Grammar <doc/lang_ref.rst#formal-grammar>`_
    * `Using Generated Code <doc/using_generator.rst>`_
        * `Compile with the CLI <doc/using_generator.rst#compile-with-the-cli>`_
        * `Python Guide <doc/using_generator.rst#python-guide>`_
    * `Managing Specs <doc/managing_specs.rst>`_
        * `Using Namespaces <doc/managing_specs.rst#using-namespaces>`_
        * `Splitting a Namespace Across Files <doc/managing_specs.rst#splitting-a-namespace-across-files>`_
        * `Using Header Files <doc/managing_specs.rst#using-header-files>`_
        * `Separating Public and Private Routes <doc/managing_specs.rst#separation-public-and-private-routes>`_
    * `Evolving a Spec <doc/evolve_spec.rst>`_
        * `Background <doc/evolve_spec.rst#background>`_
        * `Sender-Recipient <doc/evolve_spec.rst#sender-recipient>`_
        * `Backwards Incompatible Changes <doc/evolve_spec.rst#backwards-incompatible-changes>`_
        * `Backwards Compatible Changes <doc/evolve_spec.rst#backwards-compatible-changes>`_
        * `Planning for Backwards Compatibility <doc/evolve_spec.rst#planning-for-backwards-compatibility>`_
        * `Leader-Clients <doc/evolve_spec.rst#leader-clients>`_
        * `Route Versioning <doc/evolve_spec.rst#route-versioning>`_
    * `Writing a Generator (.stoneg.py) <doc/generator_ref.rst>`_
        * `Using the API Object <doc/generator_ref.rst#using-the-api-object>`_
        * `Creating an Output File <doc/generator_ref.rst#creating-an-output-file>`_
        * `Emit Methods <doc/generator_ref.rst#emit-methods>`_
        * `Indentation <doc/generator_ref.rst#indentation>`_
        * `Examples <doc/generator_ref.rst#examples>`_
    * `JSON Serializer <doc/json_serializer.rst>`_
    * `Network Protocol <doc/network_protocol.rst>`_

.. _motivation:

Motivation
==========

Being an API designer is tough. There are an innumerable number of protocols
and serialization formats that two hosts can use to communicate. Today, JSON
over HTTP is gaining popularity, but just a few years ago, XML was the
standard. To compound the issue, developers need to support an increasing
number of language-specific SDKs to gain wide adoption.

Stone seeks to:

    1. Define API endpoints in terms of input and output data types that can
       be consistently implemented in different protocols and languages.
    2. Offer structs (product types) and tagged unions (sum types) as fundamental
       data types for modeling APIs flexibly, but strictly.
    3. Improve the visibility developers have into their APIs by centralizing
       specification and documentation.

Assumptions
-----------

Stone makes no assumptions about the protocol layer being used to make API
requests and return responses; its first use case is the Dropbox v2 API which
operates over HTTP. Stone does not come with nor enforce any particular RPC
framework.

Stone makes some assumptions about the data types supported in the serialization
format and target programming language. It's assumed that there is a capacity
for representing dictionaries (unordered string keys -> value), lists, numeric
types, and strings. The intention is for Stone to map to a multitude of
serialization formats from JSON to more space-efficient representations.

Stone assumes that a route (or API endpoint) can have its request and
response types defined without relation to each other. In other words, the
type of response does not change based on the input to the endpoint. An
exception to this rule is afforded for error responses.

.. _installation:

Installation
============

Download or clone StoneAPI, and run the following in its root directory::

    $ sudo python setup.py install

This will install a script ``stone`` to your PATH that can be run from the
command line::

    $ stone -h

Alternative
-----------

If you choose not to install ``stone`` using the method above, you will need
to ensure that you have the Python packages ``ply`` and ``six``, which can be
installed through ``pip``::

    $ pip install ply>=3.4 six>=1.3.0

If the ``stone`` package is in your PYTHONPATH, you can replace ``stone``
with ``python -m stone.cli`` as follows::

    $ python -m stone.cli -h

If you have the ``stone`` package on your machine, but did not install it or
add its location to your PYTHONPATH, you can use the following::

    $ PYTOHNPATH=path/to/stone python -m stone.cli -h

