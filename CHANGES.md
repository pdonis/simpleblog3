Simpleblog Change Log
=====================

Version 0.9.5
-------------

Added syntax highlighting to ``render-markdown`` extension. Also
factored out ``converter`` and ``formatter`` extentable properties
to allow further customization of markdown behavior by other
extensions.

Version 0.9.4
-------------

Streamlined construction of extended classes when extensions define
entry, page, or blog mixins.

Version 0.9.3
-------------

Added ``show-unchanged`` option to ``render-static`` command; default
is now not to output names of unchanged files to console.

Version 0.9.2
-------------

Formatted code to PEP 8 guidelines.

Updated copyright notices.

Version 0.9.1
-------------

Entry, page, and blog mixins in extension modules are now automatically
discovered when extension classes are constructed; they no longer need
to be declared explicitly. Each mixin type (entry, page, blog) now has
its own base class in ``simpleblog.extensions``.

Version 0.9
-----------

Beta Release.

Version 0.8
-----------

Fixed sorting of alphanumeric index in the ``indexes`` extension,
so that quotes and other non-alphanumeric characters are not used
in the sort key.

Added very simple italics and bold formatting to the ``title``
extension.

The ``timezone`` extension now allows for changing the time zone
of your blog. This only works if the ``timestamps`` extension is
used to cache entry time stamps; the time zone name of each entry
is stored in the cache, so it stays the same if the blog's default
time zone is later changed.

Changed some config variable names for the ``publish`` command.

Added ``timezone`` example blog to show how the ``timezone`` and
``timestamps`` extensions are used, including handling a change of
time zone.

Version 0.7
-----------

Added support for a program config file to allow customizing things
like the source file encoding (to be something other than UTF-8;
see next item).

Standardized use of unicode internally for content. Source content
(blog entries, templates, metadata, and configs) is loaded using
the encoding specified in the program config file (see above; the
default is UTF-8); output content (statically rendered pages) is
encoded using the charset specified in the blog metadata (again
the default is UTF-8 if none is specified).

Switched to the PyYAML ``safe_load`` function for loading blog config
and metadata.

Added config setting in ``categories`` extension to allow customizing
the link or text to appear as the "category" link for entries that
have no category.

Added ``copyright`` extension to automatically generate copyright
metadata based on starting and ending year of blog entries.

Fixed ``localize`` extension to use blog metadata instead of config
settings.

Updated required blog metadata for extensions that need specific
keys to be present.

Version 0.6
-----------

Added ``serve-local`` command to serve statically rendered blog
on localhost for testing.

Added ``publish`` command to publish blog over SSH to a remote
host that will serve it.

Commands can now use the ``config_vars`` mechanism the same way
extensions do.

Added support for user-defined commands and extensions.

The ``simpleblog-run`` script now displays command-specific help
if a command is provided along with the ``--help`` option.

Added support for "next source" and "previous source" links on
index pages; the ``archives``, ``categories``, and ``tags``
extensions all use this feature to allow linking between index
pages for those source types.

The ``indexes`` extension now puts a line break between links,
to make the generated HTML more readable.

The ``links`` extension now makes entry links visible in the page
as well as the entry, for more options when formatting single-entry
pages. It also now adds ``title`` attributes to the links (this can
be disabled by setting the title template configs to empty values).

The ``paginate`` extension now has a config setting to include the
"next source" and "previous source" links in the page links it
generates, for easier formatting when both features are in use.

The separator for container links is now configurable.

Version 0.5
-----------

Added ``indexes`` extension to add alphabetical, chronological,
and/or key index pages to blog; these pages have links to all blog
entries in the appropriate order.

Added ``paginate`` extension to allow splitting sources with many
entries into multiple pages.

The ``title`` extension now caches entry titles.

Titles and headings for index pages are now configurable.

The template for container links (used by various extensions that
call the ``get_links`` API) is now configurable. (The API function
itself is now a method of the ``BlogExtension`` class.)

The ``feed`` extension now supports customized templates for the
unique ids that label entries and for the category elements of
entries.

You can now use hyphens instead of underscores in extension and
command names; the hyphens will be converted to underscores before
looking for extension or command modules (since module names must
be valid identifiers).

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

The ``render_static`` command now checks file sizes to determine if
pages are unchanged; it only compares the actual page data if the file
size is unchanged.

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
