#!/usr/bin/env python
"""
Package SIMPLEBLOG -- Simple Python blog system
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from collections import defaultdict
from datetime import datetime
from functools import wraps
from operator import attrgetter

from yaml import load

from plib.stdlib.builtins import first
from plib.stdlib.decotools import (
    cached_method, cached_property, memoize_generator)
from plib.stdlib.iters import suffixed_items
from plib.stdlib.version import version_string


__version__ = (0, 1)


# CONFIG

class BlogError(Exception):
    pass

class BlogConfigError(BlogError):
    pass


class BlogConfig(object):
    """Blog configuration.
    """
    
    settings = {}
    
    def __init__(self, filename=None):
        self.filename = filename or "config.yaml"
        if os.path.isfile(self.filename):
            with open(self.filename, 'rU') as f:
                self.settings = load(f)
        
        # This will prove to be convenient
        self.get = self.settings.get
    
    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError:
            raise AttributeError


# BASE


class BlogObject(object):
    """Base object for items managed by blog.
    """
    
    def __init__(self, blog):
        self.blog = blog
        self.config = self.blog.config
    
    @cached_property
    def entries_dir(self):
        return self.config.get('entries_dir', "entries")
    
    @cached_property
    def entry_ext(self):
        return self.config.get('entry_ext', ".html")
    
    @cached_property
    def template_dir(self):
        return self.config.get('template_dir', "templates")
    
    @cached_method
    def template_file(self, kind, format):
        return os.path.join(self.template_dir, "{0}.{1}".format(kind, format))
    
    @cached_method
    def template_data(self, kind, format):
        with open(self.template_file(kind, format), 'rU') as f:
            return f.read()


extension_types = {}

extension_map = defaultdict(list)

noresult = object()  # marker for no result returned

noreturn = object()  # marker for no return value at all


def check_extensions(instance, etype, key,
                     args=None, kwargs=None, result=noresult, modifying=False):
    args = args or ()
    kwargs = kwargs or {}
    for extension in extension_map.get(etype, ()):
        ext = getattr(extension, key, None)
        if ext is not None:
            if result is noreturn:
                ext(instance, *args, **kwargs)
            elif modifying:
                result = ext(instance, result, *args, **kwargs)
            else:
                result = ext(instance, *args, **kwargs)
            if (not modifying) and (result not in (noresult, noreturn)):
                break
    return result


class extendable_attr(object):
    """Base class for attributes that will use the extension mechanism.
    
    An instance of this class is applied as a decorator to mark a
    property or method of an extendable class that will use the
    extension mechanism. The instance wraps the function that
    implements the base property or method when it is called as
    a decorator. Arguments to the decorator give decorators that
    will be applied to the fully implemented property or method.
    Note that even if there are no arguments, the decorator must
    be applied with a call, like so:
    
    @extendable_property()
    def prop(self):
        ...
    """
    
    attrtype = None
    
    def __init__(self, *decorators):
        self._decorators = decorators
    
    def __call__(self, func):
        # What happens when this class is called as a decorator
        self._func = func
        return self
    
    def make_method(self, etype, name):
        assert name == self._func.__name__
        getkey = '{0}_get_{1}'.format(etype, name)
        modkey = '{0}_mod_{1}'.format(etype, name)
        @wraps(self._func)
        def meth(innerself, *args, **kwargs):
            # Check for extensions that might override the original function
            result = check_extensions(innerself, etype, getkey, args, kwargs)
            # Only call original function if no extension overrode it
            if result is noresult:
                result = self._func(innerself, *args, **kwargs)
            # Now check for extensions that want to modify the result
            result = check_extensions(innerself, etype, modkey, args, kwargs,
                result, True)
            return result
        return meth
    
    def as_extended(self, cls, name):
        meth = self.make_method(cls.extension_type, name)
        for d in reversed(self._decorators):
            # Reversing makes the declaration order more intuitive
            meth = d(meth)
        return self.attrtype(meth)


class extendable_property(extendable_attr):
    """Property to be fully implemented by ``extendable`` class decorator.
    """
    
    attrtype = cached_property


class extendable_method(extendable_attr):
    """Method to be fully implemented by ``extendable`` class decorator.
    """
    
    attrtype = cached_method


def extend_attributes(cls):
    """Implement all extendable attributes in cls.
    """
    
    for key in dir(cls):
        attr = getattr(cls, key)
        if isinstance(attr, extendable_attr):
            setattr(cls, key, attr.as_extended(cls, key))


def extendable(cls):
    """Class decorator to implement extendable properties.
    """
    
    # Determine extension type and add to map
    etype = cls.__name__.lower()
    eprefix = 'blog'
    if len(etype) > len(eprefix):
        etype = etype[len(eprefix):]
    cls.extension_type = etype
    extension_types[etype] = cls
    
    # Implement all extendable attributes
    extend_attributes(cls)
    
    # Implement post_init call at end of constructor
    initkey = '{}_post_init'.format(etype)
    oldinit = cls.__init__
    @wraps(oldinit)
    def _newinit(self, *args, **kwargs):
        oldinit(self, *args, **kwargs)
        check_extensions(self, etype, initkey, result=noreturn)
    cls.__init__ = _newinit
    
    return cls


# ENTRY

weekdaynames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

monthnames = [None,
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

html_newline = '\n'  # FIXME find out markdown's newline spec


@extendable
class BlogEntry(BlogObject):
    """Single blog entry.
    """
    
    sourcetype = 'entry'
    multisource = None
    
    def __init__(self, blog, name):
        BlogObject.__init__(self, blog)
        self.cachekey = self.name = name
        self.urlpath = "/{}".format(name)
        self.heading = "Single Entry"
        self.metadata = {}
    
    @extendable_property()
    def title(self):
        return self.name
    
    @extendable_property()
    def filename(self):
        return os.path.join(self.entries_dir, self.cachekey + self.entry_ext)
    
    @extendable_property()
    def timestamp(self):
        return datetime.fromtimestamp(os.path.getmtime(self.filename))
    
    @cached_property
    def timestamp_vars(self):
        t = self.timestamp
        return dict(
            year=t.year,
            month=t.month,
            day=t.day,
            hour=t.hour,
            minute=t.minute,
            second=t.second,
            weekdayname=weekdaynames[t.weekday()],
            monthname=monthnames[t.month]
        )
    
    @cached_property
    def timestamp_template(self):
        return self.config.get('timestamp_template',
            "{hour:02d}:{minute:02d}")
    
    @extendable_property()
    def timestamp_formatted(self):
        return self.timestamp_template.format(**self.timestamp_vars)
    
    @cached_property
    def datestamp_template(self):
        return self.config.get('datestamp_template',
            "{weekdayname}, {day:02d} {monthname} {year}")
    
    @extendable_property()
    def datestamp_formatted(self):
        return self.datestamp_template.format(**self.timestamp_vars)
    
    # Note that source is *not* an extendable property! It must
    # always be the actual source loaded from the filesystem,
    # or whatever other source is being used. Mixins should
    # override _get_source instead, to ensure that the caching
    # mechanism works properly.
    
    @cached_property
    def source(self):
        return self._get_source()
    
    def _get_source(self):
        with open(self.filename, 'rU') as f:
            return f.read()
    
    # Load is also *not* extendable, because it must be callable
    # from any code that needs to ensure that the actual data is
    # loaded. Mixins should override _do_load.
    
    @cached_method
    def load(self):
        """Load raw data.
        """
        return self._do_load()
    
    def _do_load(self):
        return self.source
    
    # Render is not extendable because, like load, it needs to be
    # callable from any code that needs to render raw data. Mixins
    # should override _do_render.
    
    @cached_method
    def render(self, rawdata):
        """Convert raw data into rendered data.
        """
        return self._do_render(rawdata)
    
    def _do_render(self, rawdata):
        return rawdata
    
    @extendable_property()
    def rendered(self):
        return self.render(self.load())
    
    @extendable_method()
    def body(self, format, params):
        return self.rendered
    
    @cached_method
    def make_permalink(self, format):
        return "{}.{}".format(self.urlpath, format)
    
    @extendable_method()
    def attrs(self, format, params):
        return dict(
            name=self.name,
            cachekey=self.cachekey,
            urlpath=self.urlpath,
            title=self.title,
            body=self.body(format, params),
            year=self.timestamp.year,
            month=self.timestamp.month,
            day=self.timestamp.day,
            hour=self.timestamp.hour,
            minute=self.timestamp.minute,
            timestamp=self.timestamp_formatted,
            datestamp=self.datestamp_formatted,
            permalink=self.make_permalink(format),
            **self.metadata
        )
    
    @extendable_method()
    def template(self, format):
        return self.template_data("entry", format)
    
    @extendable_method()
    def formatted(self, format, params):
        return self.template(format).format(**self.attrs(format, params))


# CONTAINERS


class BlogEntries(BlogObject):
    """Container for a set of blog entries.
    """
    
    sourcetype = None
    multisource = None
    urlshort = None
    
    def __init__(self, blog):
        BlogObject.__init__(self, blog)
    
    def _get_entries(self):
        raise NotImplementedError
    
    @cached_property
    def entry_sort_key(self):
        return self.config.get('entry_sort_key', 'timestamp')
    
    @cached_property
    def entry_sort_reversed(self):
        return self.config.get('entry_sort_reversed', True)
    
    @cached_property
    def entries(self):
        return sorted(self._get_entries(),
            key=attrgetter(self.entry_sort_key),
            reverse=self.entry_sort_reversed
        )
    
    def _get_urlpath(self):
        if self.urlshort is not None:
            return "{}index".format(self.urlshort)
        raise NotImplementedError
    
    @cached_property
    def urlpath(self):
        return self._get_urlpath()


class BlogIndex(BlogEntries):
    
    sourcetype = 'blog'
    title = "Home"
    heading = "Home Page"
    urlshort = "/"
    
    def _get_entries(self):
        return self.blog.all_entries


# PAGES


def prefixed_keys(mapping, prefix):
    """Return dict with all keys prefixed by ``prefix``.
    """
    tmpl = prefix + "{}"
    return mapping.__class__(
        (tmpl.format(key), mapping[key])
        for key in mapping
    )


class BlogEntryParams(object):
    """Convenience object to store format parameters.
    """
    
    def __init__(self, mapping=None, **kwargs):
        self.update(mapping, **kwargs)
    
    def update(self, mapping=None, **kwargs):
        for obj in (mapping, kwargs):
            if obj:
                for k, v in obj.iteritems():
                    setattr(self, k, v)


@extendable
class BlogPage(BlogObject):
    """Single page containing one or more entries.
    """
    
    def __init__(self, blog, source, format, pagenum=None):
        BlogObject.__init__(self, blog)
        self.source = source
        if isinstance(source, BlogEntry):
            self.entries = [source]
        else:
            self.entries = source.entries
        self.format = format
        self.pagenum = pagenum
        if self.pagenum and (self.pagenum > 1):
            pagemarker = self.pagenum
        else:
            pagemarker = ""
        self.urlpath = "{0}{1}.{2}".format(
            source.urlpath, pagemarker, format)
    
    # The format_entries generator is not extendable;
    # mixins can override _get_format_entries
    
    @memoize_generator
    def format_entries(self):
        return self._get_format_entries()
    
    @extendable_method()
    def entry_params(self, entry):
        return BlogEntryParams()
    
    def _get_format_entries(self):
        for entry in self.entries:
            yield entry.formatted(self.format, self.entry_params(entry))
    
    @cached_property
    def no_entries(self):
        return self.config.get('no_entries_content', "<p>No entries found!</p>")
    
    @extendable_property()
    def body(self):
        if self.entries:
            return html_newline.join(self.format_entries())
        return self.no_entries
    
    @extendable_property()
    def template(self):
        return self.template_data("page", self.format)
    
    @extendable_property()
    def attrs(self):
        metadata = dict(
            title=self.source.title,
            heading=self.source.heading,
            entries=self.body
        )
        return dict(
            prefixed_keys(self.blog.metadata, 'blog_'),
            sys_gen_name='simpleblog',
            sys_gen_uri="http://pypi.python.org/pypi/simpleblog",
            sys_gen_version=version_string(__version__),
            **prefixed_keys(metadata, 'page_')
        )
    
    @extendable_property()
    def formatted(self):
        return self.template.format(**self.attrs)


# BLOG


class BlogMetadataError(BlogError):
    pass


@extendable
class Blog(BlogObject):
    """The entire blog.
    """
    
    def __init__(self, config, filename=None):
        self.blog = self
        self.config = config
        self.filename = filename or "blog.yaml"
        self.metadata = {}
        if os.path.isfile(self.filename):
            with open(self.filename, 'rU') as f:
                self.metadata.update(load(f))
        for key in self.required_metadata:
            if key not in self.metadata:
                raise BlogMetadataError("{} missing from blog metadata".format(key))
        for key, value in self.default_metadata.iteritems():
            self.metadata.setdefault(key, value.format(**self.metadata))
    
    @extendable_property()
    def required_metadata(self):
        return set()
    
    @extendable_property()
    def default_metadata(self):
        return {}
    
    @cached_property
    def entry_class(self):
        return extension_types['entry']
    
    @cached_method
    def filter_entries(self, path):
        return suffixed_items(os.listdir(path), self.entry_ext)
    
    @extendable_property()
    def all_entries(self):
        return [
            self.entry_class(self, name)
            for name in self.filter_entries(self.entries_dir)
        ]
    
    @cached_property
    def page_class(self):
        return extension_types['page']
    
    @extendable_property()
    def index_formats(self):
        return set(self.config.get('index_formats', ["html"]))
    
    @extendable_property()
    def entry_formats(self):
        return set(self.config.get('entry_formats', ["html"]))
    
    @extendable_property()
    def sources(self):
        
        self.index_entries = BlogIndex(self)
        
        return [
            (self.index_entries, format)
            for format in self.index_formats
        ] + [
            (entry, format)
            for entry in self.all_entries
            for format in self.entry_formats
        ]
    
    @extendable_property()
    def pages(self):
        return [
            self.page_class(self, source, format)
            for source, format in self.sources
        ]


# COMMANDS


def first_subclass(o, c):
    """Return first object in o that is a subclass of c
    """
    return first(
        obj for obj in vars(o).itervalues()
        if (obj is not c)
        and isinstance(obj, type)
        and issubclass(obj, c)
    )


def load_sub(subtype, name, err, subcls):
    # FIXME allow subtype objects to "live" in other places as well
    from importlib import import_module
    try:
        mod = import_module("simpleblog.{0}s.{1}".format(subtype, name))
    except ImportError:
        raise err("{0} {1} not found!".format(subtype, name))
    klass = first_subclass(mod, subcls)
    if not klass:
        raise err("no {0} in {1} module!".format(subtype, name))
    return mod, klass


class BlogExtensionError(BlogError):
    pass


def initialize(config):
    extensions = config.get("extensions", ())
    if extensions:
        from simpleblog.extensions import BlogExtension
        # This hack is useful for extensions that need to access the
        # config in module or class level code, e.g., in decorators
        BlogExtension.config = config
        for extname in extensions:
            mod, klass = load_sub("extension", extname,
                BlogExtensionError, BlogExtension)
            mod.extension = klass(config)


def load_blog(opts):
    config = BlogConfig(opts.configfile)
    initialize(config)
    blog = extension_types['blog'](config, opts.blogfile)
    return config, blog


class BlogCommandError(BlogError):
    pass


global_optlist = (
    ("-c", "--configfile",
        { 'help': "the configuration file name (defaults to config.yaml)" }
    ),
    ("-b", "--blogfile",
        { 'help': "the blog metadata file name (defaults to blog.yaml)" }
    )
)

global_arglist = (
    ("command", { 'nargs': "?", 'default': "" }),
)


def run(cmdname, result=None, remaining=None):
    from simpleblog.commands import BlogCommand
    mod, klass = load_sub("command", cmdname,
        BlogCommandError, BlogCommand)
    
    optlist = klass.options or ()
    arglist = klass.arguments or ()
    description = klass.description
    epilog = klass.epilog
    if optlist or arglist or remaining:
        from plib.stdlib.options import parse_options
        opts, args = parse_options(
            optlist, arglist, description, epilog, remaining, result
        )
    else:
        from plib.stdlib.options import prepare_specs, make_objs
        optlist, arglist = prepare_specs(global_optlist, global_arglist)
        opts, args = make_objs(result, optlist, arglist)
    
    cmd = klass(opts, args)
    config, blog = load_blog(opts)
    cmd.run(config, blog)
