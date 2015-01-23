********************
Managing Large Specs
********************

Here we cover several strategies for dealing with a large number of routes
and types.

.. using-namespaces:

Using Namespaces
================

Whenever possible, group related routes and their associated data types into
namespaces. This organizes your API into logical groups.

Code generators should translate your namespaces into logical groups in the
target language. For example, the Python generator creates a separate Python
module for each namespace.

.. splitting-namespace:

Splitting a Namespace Across Files
==================================

If a spec is growing large and unwieldy with thousands of lines, it might make
sense to split the namespace across multiple spec files.

All you need to do is create multiple ``.babel`` files with the same
`namespace <write_spec.rst#namespace>`_ definition. Code generators cannot
distinguish between spec files--only namespaces--so no code will be affected.

As explained in `Choosing a Filename <write_spec.rst#filename>`_, when
splitting a namespace across multiple files, each file should use the namespace
name as a prefix of its filename.

The ``babelapi`` command-line interface makes it easy to specify multiple
specs::

    $ babelapi python spec1.babel spec2.babel spec3.babel output/
    $ babelapi python *.babel output/

.. using-headers:

Using Header Files
==================

If multiple spec files depend on the same user-defined type or alias, then you
should move the common definition to a header file.

Headers files have a ``.babelh`` extension. They're identical to regular
``.babel`` specs in contents, except that they cannot define a namespace nor
routes.

Assuming that the header file is named ``common.babelh``, specify
``include common`` after the namespace definition in your spec to get access
to all data types defined in the header. These data types will be imported into
the global environment of the spec file and will not require any reference to
``common``.

.. public-private:

Separating Public and Private Routes
====================================

Most services have a set of public routes that they publish for external
developers, as well as a set of private routes that are intended to only be
used internally by first-party apps.

To use Babel for both public and private routes, we recommend splitting specs
into ``{namespace}_public.babel`` and ``{namespace}_private.babel`` files. You
may choose to simply use ``{namespace}.babel`` to represent the public spec.

When publishing your API to third-party developers, you can simply include the
public spec file. When generating code for internal use, you can use both the
public and private spec files.
