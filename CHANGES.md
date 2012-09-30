Simpleblog Change Log
=====================

Version 0.4
-----------

Added ``timezone`` extension to make entry timestamps timezone-aware
(without this extension they are "naive" ``datetime`` objects).
Refactored entry class and timestamps extension APIs to enable this
extension to work easily. The ``timezone_name`` config setting lets
you explicitly declare your blog's timezone. This extension requires
the ``pytz`` library.

Added ``utc_timestamps`` config setting, to make entry timestamps
use UTC instead of the system's local timezone. This functionality is
only used if the ``timezone`` extension is not loaded; if that extension
is used, the ``utc_timestamps`` config is only used if there is no
explicit ``timezone_name`` config given, to tell the extension which
timezone to use (UTC or system local) when making "aware" ``datetime``
objects.

Version 0.3
-----------

All properties of entry objects are now either extendable or
configurable except for ``cachekey``, which needs to be hard-coded,
and ``source`` (see comments in the source code for discussion of
that one).

Properties loaded from config settings can now be declared in a
``config_vars`` class attribute, without having to write the
boilerplate property definition code each time.

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
