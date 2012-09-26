Simpleblog Change Log
=====================

Version 0.3
-----------

All properties of entry objects are now either extendable or
configurable except for ``cachekey``, which needs to be hard-coded,
and ``source`` (see comments in the source code for discussion of
that one).

Factored out ``simpleblog.run`` module for running commands, so
unnecessary code is not loaded in the interactive shell.

The template used for category links in the ``categories``
extension is now configurable.

Simpleblog now uses the ``setuputils`` helper module to automate
away the boilerplate in its ``setup.py`` script.

Version 0.2
-----------

JSON format is now supported for config and blog metadata files,
so the PyYAML package is no longer required (though it will still
be used if it is available).

Weekday and month names are now localized using the current locale;
also added support for long names.

Added support for archived feeds per RFC 5005. Only Atom feeds are
archived (RSS doesn't appear to support this).

Template files for feeds now have defaults in the ``simpleblog``
package, so you do not need to define them yourself.

Feed link templates are now loaded from template files instead of
being hard-coded in the Python source.

Markdown output format and "pretty-printing" of output are now
configurable.

Added another example blog.

Various minor fixes to remove potential bugs or improve code
portability.

Version 0.1
-----------

Initial release.
