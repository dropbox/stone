**************
Managing Specs
**************

Here we cover several strategies for dealing with larger projects composed of
many specs, routes, and user-defined types.

Using Namespaces
================

Whenever possible, group related routes and their associated data types into
namespaces. This organizes your API into logical groups.

Code generators should translate your namespaces into logical groups in the
target language. For example, the Python generator creates a separate Python
module for each namespace.

Splitting a Namespace Across Files
==================================

If a spec is growing large and unwieldy with thousands of lines, it might make
sense to split the namespace across multiple spec files.

All you need to do is create multiple ``.babel`` files with the same
`Namespace <lang_ref.rst#namespace>`_ definition. Code generators cannot
distinguish between spec files--only namespaces--so no code will be affected.

When splitting a namespace across multiple spec files, each file should use the
namespace name as a prefix of its filename.

The ``babelapi`` command-line interface makes it easy to specify multiple
specs::

    $ babelapi python spec1.babel spec2.babel spec3.babel output/
    $ babelapi python *.babel output/

Using Header Files
==================

If multiple spec files depend on the same user-defined type or alias, then you
should move the common definition to a header file.

See how to use `Include <doc/lang_ref.rst#include>`_.

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
