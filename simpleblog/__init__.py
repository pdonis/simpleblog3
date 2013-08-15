#!/usr/bin/env python3
"""
Package SIMPLEBLOG -- Simple Python blog system
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
import pkgutil
from codecs import decode, encode
from collections import defaultdict
from datetime import datetime
from functools import wraps
from operator import attrgetter

from plib.stdlib.decotools import (
    cached_method, cached_property, memoize_generator)
from plib.stdlib.ini import PIniFile
from plib.stdlib.ini.defs import *
from plib.stdlib.iters import suffixed_items
from plib.stdlib.localize import (
    weekdayname, weekdayname_long,
    monthname, monthname_long)


__version__ = "0.9.6"


blogfile_exts = ["json"]

try:
    from yaml import load as _loads
except ImportError:
    from json import loads
else:
    blogfile_exts.insert(0, "yaml")
    
    from functools import partial
    
    try:
        # Use libyaml if present, much faster
        from yaml import CSafeLoader as _Loader
    except ImportError:
        from yaml import SafeLoader as _Loader
    
    # Make PyYAML load unicode strings
    _Loader.add_constructor(
        'tag:yaml.org,2002:str',
        lambda self, node: self.construct_scalar(node)
    )
    
    loads = partial(_loads, Loader=_Loader)


inifile = PIniFile("simpleblog", [
    ('source', [
        ('encoding', INI_STRING, 'utf-8')
    ])
])


def blogdata(data, encoding=inifile.source_encoding):
    return decode(data, encoding)


def read_blogfile(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    return blogdata(data)


def load_blogfile(filename, basename, mapping):
    trial_names = [filename] + [
        "{0}.{1}".format(basename, ext)
        for ext in blogfile_exts
    ]
    for fname in trial_names:
        if fname and os.path.isfile(fname):
            mapping.update(loads(read_blogfile(fname)))
            break


# CONFIG

newline = os.linesep


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


class shared_property(object):
    """Decorator for cached property shared among all instances of a class.
    """
    
    def __init__(self, fget, name=None, doc=None):
        self.__fget = fget
        self.__name = name or fget.__name__
        self.__doc__ = doc or fget.__doc__
    
    def __get__(self, instance, cls):
        if instance is None:
            return self
        result = self.__fget(instance)
        # This is the key difference from cached_property; the value can only
        # be looked up on an instance, but once we have it, we set it on the
        # class so all instances will see the same value
        setattr(cls, self.__name, result)
        return result


def make_config_property(key, value):
    """Return``shared_property`` for config setting.
    
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
    return shared_property(fget)


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
        for key, value in attrs.get('config_vars', {}).items():
            # The make_config_property function is factored out
            # to ensure each closure it returns is "clean"
            setattr(cls, key, make_config_property(key, value))


class BlogConfigUser(object, metaclass=BlogConfigUserMeta):
    """Base class for objects that use a config.
    """
    
    def __init__(self, config):
        self.config = config


# BASE


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
    
    @cached_function
    def template_basename(self, kind, format):
        return "{0}.{1}".format(kind, format)
    
    @cached_method
    def template_file(self, kind, format):
        return os.path.join(self.template_dir, self.template_basename(kind, format))
    
    @cached_method
    def template_data(self, kind, format):
        try:
            return read_blogfile(self.template_file(kind, format))
        except IOError:
            try:
                return blogdata(pkgutil.get_data(
                    'simpleblog',
                    "templates/{}".format(self.template_basename(kind, format))
                ))
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
            result = check_extensions(
                innerself, etype, modkey, args, kwargs,
                result, True
            )
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


class BlogSource(BlogObject):
    """Base class for blog objects that can be page sources.
    """
    
    sourcetype = None
    multisource = None
    
    @cached_property
    def next_source(self):
        return self._get_next_source()
    
    def _get_next_source(self):
        return None
    
    @cached_property
    def prev_source(self):
        return self._get_prev_source()
    
    def _get_prev_source(self):
        return None


@extendable
class BlogEntry(BlogSource):
    """Single blog entry.
    """
    
    config_vars = dict(
        utc_timestamps=False,
        timestamp_template="{hour:02d}:{minute:02d}",
        datestamp_template="{year}-{month:02d}-{day:02d}"
    )
    
    sourcetype = 'entry'
    
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
    
    # Note that mtime is *not* an extendable property; it must always represent
    # the last modification time of the entry's source, in file mtime (i.e.,
    # POSIX mtime) format. Mixins should override _get_mtime instead.
    
    @cached_property
    def mtime(self):
        return self._get_mtime()
    
    def _get_mtime(self):
        return os.path.getmtime(self.filename)
    
    @extendable_method()
    def datetime_from_mtime(self, mtime):
        tf = datetime.utcfromtimestamp if self.utc_timestamps else datetime.fromtimestamp
        return tf(mtime)
    
    @extendable_property()
    def timestamp(self):
        return self.datetime_from_mtime(self.mtime)
    
    @extendable_property()
    def timestamp_attrfuncs(self):
        return dict(
            year=None,
            month=None,
            day=None,
            hour=None,
            minute=None,
            second=None,
            weekdayname=lambda t: weekdayname(t.weekday(), dt=True),
            weekdayname_long=lambda t: weekdayname_long(t.weekday(), dt=True),
            monthname=lambda t: monthname(t.month),
            monthname_long=lambda t: monthname_long(t.month)
        )
    
    @extendable_method()
    def timestamp_attrs(self, dt):
        return dict(
            (key, (varfunc or attrgetter(key))(dt))
            for key, varfunc in self.timestamp_attrfuncs.items()
        )
    
    @extendable_property()
    def timestamp_vars(self):
        return self.timestamp_attrs(self.timestamp)
    
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
        return read_blogfile(self.filename)
    
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


def make_config_or_default_property(key):
    """Return``cached_property`` for config_or_default setting.
    
    The ``key`` argument is the name of the property.
    """
    
    def fget(self):
        return self.config_or_default(key)
    fget.__name__ = key
    return cached_property(fget)


class BlogEntriesMeta(BlogConfigUserMeta):
    """Metaclass to automatically set up configs for blog entry containers.
    """
    
    def __init__(cls, name, bases, attrs):
        super(BlogEntriesMeta, cls).__init__(name, bases, attrs)
        # Similar setup to BlogConfigUserMeta, but for config_or_default_vars
        for key, value in attrs.get('config_or_default_vars', {}).items():
            setattr(cls, 'default_{}'.format(key), value)
            setattr(cls, key, make_config_or_default_property(key))


class BlogEntries(BlogSource, metaclass=BlogEntriesMeta):
    """Container for a set of blog entries.
    """
    
    config_vars = dict(
        entry_sort_key='timestamp',
        entry_sort_reversed=True
    )
    
    config_or_default_vars = dict(
        title="",
        heading=""
    )
    
    urlshort = ""
    
    @cached_method
    def config_or_default(self, key):
        default_tmpl = getattr(self, 'default_{}'.format(key))
        tmpl = self.config.get(
            '{}_{}_template'.format(self.sourcetype, key),
            default_tmpl
        ) if self.sourcetype else default_tmpl
        default_varnames = getattr(self, '{}_varnames'.format(key), {})
        varnames = self.config.get(
            '{}_{}_varnames'.format(self.sourcetype, key),
            default_varnames
        ) if self.sourcetype else default_varnames
        return tmpl.format(**dict((k, getattr(self, k)) for k in varnames))
    
    @cached_property
    def entries(self):
        return sorted(
            self._get_entries(),
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
    
    @cached_property
    def link_attrs(self):
        return self._get_link_attrs()
    
    def _get_link_attrs(self):
        return dict(
            urlshort=self.urlshort,
            urlpath=self.urlpath,
            title=self.title,
            heading=self.heading,
            count=len(self.entries)
        )
    
    @cached_property
    def sourcetype_sources(self):
        return self._get_sourcetype_sources()
    
    def _get_sourcetype_sources(self):
        return []
    
    @cached_property
    def sourcetype_index(self):
        if self.sourcetype_sources:
            return self.sourcetype_sources.index(self)
        return -1
    
    def _get_next_source(self):
        i = self.sourcetype_index
        if (i > -1) and (i < (len(self.sourcetype_sources) - 1)):
            return self.sourcetype_sources[i + 1]
        return None
    
    def _get_prev_source(self):
        i = self.sourcetype_index
        if i > 0:
            return self.sourcetype_sources[i - 1]
        return None


class BlogIndex(BlogEntries):
    
    sourcetype = 'blog'
    urlshort = "/"
    default_title = "Home"
    default_heading = "Home Page"
    
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
                for k, v in obj.items():
                    setattr(self, k, v)
    
    def get(self, key, default=None):
        return getattr(self, key, default)


@extendable
class BlogPage(BlogObject):
    """Single page containing one or more entries.
    """
    
    config_vars = dict(
        no_entries=('no_entries_content', "<p>No entries found!</p>"),
        source_link_template='<a href="{urlshort}">{title}</a>',
        source_link_sep="&nbsp;&nbsp;"
    )
    
    def __init__(self, blog, source, format):
        BlogObject.__init__(self, blog)
        self.source = source
        self.title = self.source.title
        self.heading = self.source.heading
        if isinstance(source, BlogEntry):
            self.entries = [source]
        else:
            self.entries = source.entries
        self.format = format
        self.urlpath = "{0}.{1}".format(source.urlpath, format)
    
    @cached_property
    def filepath(self):
        return os.path.join(
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
            return newline.join(self.format_entries())
        return self.no_entries
    
    @extendable_property()
    def template(self):
        return self.template_data("page", self.format)
    
    @extendable_property()
    def link_source(self):
        return self.source
    
    @cached_property
    def source_links(self):
        """Return HTML links to next and previous sources.
        """
        source = self.link_source
        return tuple(
            self.source_link_template.format(**s.link_attrs) if s else ""
            for s in ((source.next_source, source.prev_source) if source else (None, None))
        )
    
    @extendable_property()
    def attrs(self):
        links = (link_next_source, link_prev_source) = self.source_links
        metadata = dict(
            title=self.title,
            heading=self.heading,
            entries=self.body,
            sourcelinks=self.source_link_sep.join(link for link in links if link),
            sourcelink_next=link_next_source,
            sourcelink_prev=link_prev_source
        )
        return dict(
            prefixed_keys(self.blog.metadata, 'blog_'),
            sys_gen_name='simpleblog3',
            sys_gen_uri="http://pypi.python.org/pypi/simpleblog3",
            sys_gen_version=__version__,
            **prefixed_keys(metadata, 'page_')
        )
    
    @extendable_property()
    def formatted(self):
        return self.template.format(**self.attrs)
    
    @cached_property
    def encoded(self):
        return encode(self.formatted, self.blog.metadata['charset'])


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
        for key, value in self.default_metadata.items():
            self.metadata.setdefault(key, value.format(**self.metadata))
    
    @extendable_property()
    def required_metadata(self):
        return set()
    
    @extendable_property()
    def default_metadata(self):
        return dict(
            charset='utf-8'
        )
    
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
    
    @extendable_property()
    def render_items(self):
        return [(page.encoded, page.filepath) for page in self.pages]


# INITIALIZATION


def initialize(config):
    extensions = config.get("extensions", ())
    if extensions:
        from simpleblog.ext import load
        load(config, extensions)


def load_blog(opts):
    config = BlogConfig(opts.configfile)
    initialize(config)
    blog = extension_types['blog'](config, opts.blogfile)
    return config, blog
