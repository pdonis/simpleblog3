Simpleblog
==========

Simpleblog is a simple Python blogging system. I use it to write
and publish my own blog at http://blog.peterdonis.com. I wrote
it because I couldn't find an existing blogging system that made
it sufficiently easy to write, format, and publish my blog.

My chief goal with ``simpleblog`` is for the system to stay out
of my way; I want to be able to add features easily, but other
than when I'm actually doing that, I want simpleblog to "just
work", so I don't even have to think about it at all. That way
I can think about what I'm writing instead. With the existing
systems I've tried, I have ended up spending too much time
figuring out the internals of the system in order to get things
the way I want them. Admittedly, I have not tried many existing
systems; but what I have read about the ones I haven't tried
has not encouraged me that any of them would work any better
for me. So here we are.

If you just want to start using ``simpleblog``, without digging
into its internal details, then once you've installed it, you can
copy the contents of one of the example blogs to a directory of
your choice, and start writing your blog there. The layout of
the example blogs, and the files in them, will give you a start.
Before writing any entries, you will want to at least edit the
``blog.json`` or ``blog.yaml`` file to customize your blog's
metadata, and the template files in the ``templates``
subdirectory, which give extremely plain HTML pages by default.

Note that in order to use ``simpleblog``, you will need to have
installed ``plib`` (my library of useful Python stuff, which is
used in a number of places in ``simpleblog``). It is available
from the Python Package Index at http://pypi.python.org/pypi/plib.
If you want to use YAML instead of JSON for your config and blog
metadata files (I certainly find YAML much easier to type since
I hate typing delimiters, as you will know if you read my blog),
you will also need to have installed PyYAML, the YAML parsing
library for Python (which in my opinion should be in the Python
standard library).

Simpleblog's Architecture
-------------------------

The structure of ``simpleblog`` is simple (no, that wasn't intended
to be humor, it's just the way it naturally came out). There
are five core object types: the config, the blog, pages, containers,
and entries. The config lets you define or customize the internal
behavior of the code, and all the other objects have a reference
to it. The other object types fall into a simple hierarchy:

- The blog contains one or more pages, plus metadata which can be
  specified in a separate file from the config file (the default
  filenames are ``blog.yaml`` (or ``blog.json``) and ``config.yaml``
  (or ``config.json``), but other filenames can be passed on the
  command line to the ``simpleblog-run`` script--see below);

- Each page wraps a "source", which can be either a single entry,
  or a container;

- A container contains one or more entries that have something in
  common;

- An entry is the actual content.

It's important to note that the above is *all* that the core
objects implement, and it is completely general. Everything
specific, such as what actual "sources" there are, which entries
are in which containers, etc., is all defined in extensions.
(Strictly speaking, there is one default container in every blog,
which simply contains all its entries, and every blog has an
index page, which uses that container as its "source", plus a
page for every individual entry. But that's *all* that is in
the blog by default. Of course, that by itself is enough to
have a simple blog, which is part of the point.)

### Templates

Simpleblog uses Python's built-in string templating and formatting
to render entries and pages. The example blogs illustrate the
basics of how this works. This is one area where I do *not* have
any items on my To Do list; the various fancy templating engines
out there have their uses for highly dynamic web applications,
but for a simple blog they are, in my opinion, extreme overkill.
But the extension mechanism is there for anyone who disagrees
and wants to use their favorite templating engine.

### Extensions

Extensions allow pretty much every behavior of the four blog
object types--everything above except the config--to be changed,
and even allow new behaviors to be added. (I say "pretty much"
only because I can't be absolutely positive I have allowed for
every possibility; but that's my goal.) This is done with a
simple (yes, you'll see that word cropping up a lot...) but
powerful mechanism. You write a Python module that contains a
subclass of the ``BlogExtension`` class, and implements your
desired changed or added behaviors, and add its name to the
list of extensions in your config file. That's it. Or, of
course, you can use one of the extensions that come with
simpleblog, listed below. I use all of them for my blog. They
give good examples of how the extension mechanism can be used.

(Note: Strictly speaking, since extension names will be looked
up as Python module names, they must be valid identifiers,
which means they can't include hyphens. However, ``simpleblog``
allows you to use hyphens when referring to extensions, as in
the ``render-markdown`` extension; it converts the hyphens to
underscores before looking up the module name. Command names
are handled the same way--see below.)

- The ``archives`` extension adds containers for entries that
  were published during specific time periods--years, months,
  and/or days, depending on the config settings--and adds
  archive pages to the blog for each container.

- The ``categories`` extension allows you to classify entries
  by category, and adds a container and an index page for each
  category.

- The ``feed`` extension generates feeds for your blog. Both
  RSS 2.0 and Atom feeds are supported. Currently only your
  blog's index page will have a feed generated, but extending
  that is on the To Do list (see below). This extension also
  supports archived feeds per RFC 5005 (this only works for
  Atom feeds since the RSS spec does not appear to support
  this), which lets you limit the size of your syndication
  feed file by archiving old entries.

- The ``folding`` extension allows your entries to have "short"
  versions that can appear in index pages, with links to the
  entry page that shows the entire entry (including the part
  "below the fold").

- The ``grouping`` extension allows entries on index pages to
  be grouped, so that group headers and footers can appear in
  addition to the entries themselves. The default is to group
  by date, which goes along with the default sorting of entries
  in all containers, which is reverse chronological; but these
  can be changed by config settings (of course they should both
  be changed consistently).

- The ``indexes`` extension adds index pages to your blog that
  give links to all entries in either alphabetical (by title),
  chronological, or "key" (meaning the unique key assigned to
  each entry) order.

- The ``links`` extension allows you to add links to the previous
  and next entries in your blog's containers to each entry. By
  default it only does this on single-entry pages, but this can
  be configured; also, which links actually appear on the page
  is controlled by a template you provide.

- The ``localize`` extension is currently experimental; all it
  does is add a "locale" config setting if certain other config
  settings are present. More localization functionality is
  on the To Do list; currently simpleblog is only tested with
  English ASCII text.

- The ``paginate`` extension allows splitting sources with many
  entries into multiple pages.

- The ``quote`` extension adds quoted versions of all URLS
  found in the blog's metadata. I added this because I link to
  the W3C HTML validator for my blog's index page, which wants
  quoted URLs, and this was an easy way to avoid having to type
  them into my blog metadata by hand. :)

- The ``render-markdown`` extension allows your entry source
  to be plain text using Markdown syntax; the extension then
  renders it into HTML. (Without any extension changing the
  rendering, simpleblog just uses your entry source unchanged
  as its rendered HTML.) There are config options to specify
  the output format for Markdown (the default is HTML 4) and
  to "pretty print" the output.

- The ``tags`` extension allows you to add tags to your entries,
  and adds a container and index page for each tag. This extension
  uses the caching mechanism for entry metadata (see below).

- The ``timestamps`` extension uses the caching mechanism to
  store immutable file timestamps. (Without any extension, an
  entry's timestamp is the last modified time of its source
  file, but this means if you make any change at all to an entry
  once it is published, its time stamp changes, which may change
  where it appears in index pages.)

- The ``timezone`` extension makes entry timestamps timezone-aware
  (without this extension they are "naive" ``datetime`` objects).
  The ``timezone_name`` config setting lets you explicitly declare
  your blog's timezone; otherwise your system's local time zone
  setting will be used (note, however, that the ``utc_timestamps``
  config setting can force the timezone to UTC; see notes in the
  change log). This extension requires the ``pytz`` library.

- The ``title`` extension allows you to specify a title for each
  entry in the entry's source file. (Without any extension, the
  title of an entry is the same as its relative file name or URL
  path, which is probably not what you want.)

Note that in some cases the order in which extensions are declared
in your config file matters. The order in which extensions are
listed in the config determines the order in which they are loaded,
which determines the order in which they get to process whatever
data they are processing, which can obviously make a difference
if multiple extensions process the same data. The cases you are
most likely to encounter are extensions that process the raw
entry source data (the ``title``, ``tags``, and ``folding``
extensions all do, and the ordering that is known to work is the
order in which I just gave them), and extensions that add sources
in the form of new containers (the ``archives``, ``categories``,
and ``tags`` extensions) vs. extensions that need to know all the
containers in the blog (the ``links`` extension is the key one,
and needs to be loaded after the ones listed just now).

### Entry Metadata Caching

Entry metadata is often useful for putting entries into containers
and ordering them properly. It is nice to be able to do this without
having to actually ask the filesystem for any data on individual
entries, by either statting or opening and reading the entry source
files. Simpleblog provides a caching mechanism for entry metadata
to make this simple. Just use the ``cached`` decorator on any
property that represents metadata you want cached, and provide the
name of the file the cache should be stored in.

### Commands

All of the above is nice, but in order to actually use it, you have
to have some kind of front end. The ``simpleblog-run`` script provides
one. If run without any command at all, the script simply puts you
into the Python interactive shell, with the ``simpleblog`` package
loaded; I find this extremely useful for testing and debugging. But
the script can also be enhanced with commands, by a mechanism similar
to the extension mechanism.

(Note: As with extension names, hyphens in command names are converted
to underscores before looking up the module, so you can use hyphens,
as is done below, if you find them easier to type, as I do.)

- The ``publish`` command publishes your statically rendered blog using
  SSH.

- The ``render-static`` command renders static versions of all the
  pages in your blog. A config setting controls the directory that
  the files are rendered to. For my blog, this is currently sufficient,
  since I publish it as static files.

- The ``serve-local`` command serves your statically rendered blog on
  localhost for testing.

To Do
-----

Add support for having extension and command files available
in other places besides the simpleblog sub-packages. This will
allow you to write your own and use them without having to mess
with the simpleblog installation itself.

Add fancier example blogs to show how the various extensions work.

Add support for comments while still allowing the blog to be
statically generated.

Add support for generating feeds for other container index
pages besides the blog index (e.g., categories, tags, and
archives).

Add more localization support.

Copyright and License
---------------------

SIMPLEBLOG is Copyright (C) 2012 by Peter A. Donis.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version. (See the LICENSE file for a
copy of version 2 of the License.)

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
