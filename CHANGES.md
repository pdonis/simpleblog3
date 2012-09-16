Simpleblog Change Log
=====================

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
