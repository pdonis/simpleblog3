#!/usr/bin/env python
"""
Package SIMPLEBLOG -- Simple Python blog system
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
import pkgutil
from collections import defaultdict
from datetime import datetime
from functools import wraps
from operator import attrgetter

from plib.stdlib.builtins import first
from plib.stdlib.decotools import (
    cached_method, cached_property, memoize_generator)
from plib.stdlib.iters import suffixed_items
from plib.stdlib.localize import (
    weekdayname, weekdayname_long,
    monthname, monthname_long)

from plib.stdlib.strings import universal_newline
from plib.stdlib.version import version_string


__version__ = (0, 1)


blogfile_exts = ["json"]

try:
    from yaml import load
except ImportError:
    from json import load
else:
    blogfile_exts.insert(0, "yaml")


def load_blogfile(filename, basename, mapping):
    trial_names = [filename] + [
        "{0}.{1}".format(basename, ext)
        for ext in blogfile_exts
    ]
    for fname in trial_names:
        if fname and os.path.isfile(fname):
            with open(fname, 'rU') as f:
                mapping.update(load(f))
            break


# CONFIG

class BlogError(Exception):
    pass

class BlogConfigError(BlogError):
    pass


class BlogConfig(object):
    """Blog configuration.
    """
    
    def __init__(self, filename=None):
        self.filename = filename
        self.settings = {}
        load_blogfile(self.filename, "config", self.settings)
        
        # This will prove to be convenient
        self.get = self.settings.get
    
    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError:
            raise AttributeError


def make_config_property(key, value):
    """Return``cached_property`` for config setting.
    
    The ``key`` argument is the name of the property.
    
    The ``value`` argument is either a default value, or a
    2-tuple ``(varkey, default)`` giving the key of the setting
    in the config and the default value, or a dict with one or
    more of the following keys: ``varkey``, ``default``,
    ``vartype``, where ``vartype`` gives a type to which the
    returned value will be coerced.
    """
    
    if isinstance(value, dict):
        vartype = value.get('vartype', None)
        varkey = value.get('varkey', key)
        default = value.get('default', None)
    elif isinstance(value, tuple):
        vartype = None
        varkey, default = value
    else:
        vartype = None
        varkey = key
        default = value
    if vartype is not None:
        def fget(self):
            return vartype(self.config.get(varkey, default))
    else:
        def fget(self):
            return self.config.get(varkey, default)
    fget.__name__ = key
    return cached_property(fget)


class BlogConfigUserMeta(type):
    """Metaclass to automatically set up configurable attributes.
    
    We do this with a metaclass instead of a class decorator because
    we want every subclass of ``BlogConfigUser`` to have configurable
    attributes automatically set up, without requiring the programmer
    to remember to decorate the class.
    """
    
    def __init__(cls, name, bases, attrs):
        super(BlogConfigUserMeta, cls).__init__(name, bases, attrs)
        # Only do this for config vars declared in this class
        for key, value in attrs.get('config_vars', {}).iteritems():
            # The make_config_property function is factored out
            # to ensure each closure it returns is "clean"
            setattr(cls, key, make_config_property(key, value))


class BlogConfigUser(object):
    """Base class for objects that use a config.
    """
    
    __metaclass__ = BlogConfigUserMeta
    
    def __init__(self, config):
        self.config = config


# BASE

class BlogMixin(BlogConfigUser):
    """All entry, page, and blog mixins in extensions must subclass this class.
    """
    pass


class BlogTemplateError(BlogError):
    pass


class BlogObject(BlogConfigUser):
    """Base object for items managed by blog.
    """
    
    config_vars = dict(
        entries_dir="entries",
        entry_ext=".html",
        template_dir="templates"
    )
    
    def __init__(self, blog):
        self.blog = blog
        self.config = self.blog.config  # don't need to call the superclass __init__
    
    @cached_method
    def template_basename(self, kind, format):
        return "{0}.{1}".format(kind, format)
    
    @cached_method
    def template_file(self, kind, format):
        return os.path.join(self.template_dir, self.template_basename(kind, format))
    
    @cached_method
    def template_data(self, kind, format):
        try:
            with open(self.template_file(kind, format), 'rU') as f:
                return f.read()
        except IOError:
            try:
                return pkgutil.get_data('simpleblog',
                    "templates/{}".format(self.template_basename(kind, format)))
            except IOError:
                raise BlogConfigError("template {}.{} not found".format(kind, format))


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


@extendable
class BlogEntry(BlogObject):
    """Single blog entry.
    """
    
    config_vars = dict(
        timestamp_template="{hour:02d}:{minute:02d}",
        datestamp_template="{year}-{month:02d}-{day:02d}"
    )
    
    sourcetype = 'entry'
    multisource = None
    
    def __init__(self, blog, name):
        BlogObject.__init__(self, blog)
        self.cachekey = name
        self.metadata = {}
    
    @extendable_property()
    def name(self):
        return self.cachekey
    
    @extendable_property()
    def urlpath(self):
        return "/{}".format(self.cachekey)
    
    @extendable_property()
    def heading(self):
        return "Single Entry"
    
    @extendable_property()
    def title(self):
        return self.name
    
    @extendable_property()
    def filename(self):
        return os.path.join(self.entries_dir, self.cachekey + self.entry_ext)
    
    @extendable_property()
    def timestamp(self):
        return datetime.fromtimestamp(os.path.getmtime(self.filename))
    
    @extendable_property()
    def timestamp_vars(self):
        t = self.timestamp
        return dict(
            year=t.year,
            month=t.month,
            day=t.day,
            hour=t.hour,
            minute=t.minute,
            second=t.second,
            weekdayname=weekdayname(t.weekday(), dt=True),
            weekdayname_long=weekdayname_long(t.weekday(), dt=True),
            monthname=monthname(t.month),
            monthname_long=monthname_long(t.month)
        )
    
    @extendable_property()
    def timestamp_formatted(self):
        return self.timestamp_template.format(**self.timestamp_vars)
    
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
    
    @extendable_method()
    def template(self, format):
        return self.template_data("entry", format)
    
    @cached_method
    def make_permalink(self, format):
        return "{}.{}".format(self.urlpath, format)
    
    @extendable_method()
    def attrs(self, format, params):
        return dict(
            self.timestamp_vars,
            name=self.name,
            cachekey=self.cachekey,
            urlpath=self.urlpath,
            title=self.title,
            body=self.body(format, params),
            timestamp=self.timestamp_formatted,
            datestamp=self.datestamp_formatted,
            permalink=self.make_permalink(format),
            **self.metadata
        )
    
    @extendable_method()
    def formatted(self, format, params):
        return self.template(format).format(**self.attrs(format, params))


# CONTAINERS


class BlogEntries(BlogObject):
    """Container for a set of blog entries.
    """
    
    config_vars = dict(
        entry_sort_key='timestamp',
        entry_sort_reversed=True
    )
    
    sourcetype = None
    multisource = None
    urlshort = None
    
    @cached_property
    def entries(self):
        return sorted(self._get_entries(),
            key=attrgetter(self.entry_sort_key),
            reverse=self.entry_sort_reversed
        )
    
    def _get_entries(self):
        raise NotImplementedError
    
    @cached_property
    def urlpath(self):
        return self._get_urlpath()
    
    def _get_urlpath(self):
        if self.urlshort is not None:
            return "{}index".format(self.urlshort)
        raise NotImplementedError


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
    
    config_vars = dict(
        no_entries=('no_entries_content', "<p>No entries found!</p>")
    )
    
    def __init__(self, blog, source, format):
        BlogObject.__init__(self, blog)
        self.source = source
        if isinstance(source, BlogEntry):
            self.entries = [source]
        else:
            self.entries = source.entries
        self.format = format
        self.urlpath = "{0}.{1}".format(
            source.urlpath, format)
        self.filepath = os.path.join(
            *self.urlpath[1:].split('/')
        )
    
    # The format_entries generator is not extendable;
    # mixins can override _get_format_entries
    
    @extendable_method()
    def entry_params(self, entry):
        return BlogEntryParams()
    
    @memoize_generator
    def format_entries(self):
        return self._get_format_entries()
    
    def _get_format_entries(self):
        for entry in self.entries:
            yield entry.formatted(self.format, self.entry_params(entry))
    
    @extendable_property()
    def body(self):
        if self.entries:
            return universal_newline.join(self.format_entries())
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
    
    config_vars = dict(
        index_formats=dict(
            vartype=set,
            default=["html"]),
        entry_formats=dict(
            vartype=set,
            default=["html"])
    )
    
    def __init__(self, config, filename=None):
        self.blog = self
        self.config = config
        self.metadata = {}
        load_blogfile(filename, "blog", self.metadata)
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
    
    @cached_method
    def filter_entries(self, path):
        return suffixed_items(os.listdir(path), self.entry_ext)
    
    @cached_property
    def entry_class(self):
        return extension_types['entry']
    
    @extendable_property()
    def all_entries(self):
        return [
            self.entry_class(self, name)
            for name in self.filter_entries(self.entries_dir)
        ]
    
    @extendable_method()
    def index_entries(self, format):
        return BlogIndex(self)
    
    @extendable_property()
    def sources(self):
        
        return [
            (self.index_entries(format), format)
            for format in self.index_formats
        ] + [
            (entry, format)
            for entry in self.all_entries
            for format in self.entry_formats
        ]
    
    @cached_property
    def page_class(self):
        return extension_types['page']
    
    @extendable_property()
    def pages(self):
        return [
            self.page_class(self, source, format)
            for source, format in self.sources
        ]


# INITIALIZATION

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
