#!/usr/bin/env python3
"""
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import sys
from operator import attrgetter

from plib.stdlib.builtins import first
from plib.stdlib.classtools import first_subclass
from plib.stdlib.decotools import cached_property, wraps_class
from plib.stdlib.iters import prefixed_items

from simpleblog import (
    BlogConfigUserMeta, BlogConfigUser,
    extension_types, extension_map, extend_attributes,
    BlogEntries, newline
)


class NamedEntries(BlogEntries):
    """Named container for a set of blog entries.
    """
    
    typename = None
    prefix = None
    
    sourcetype_attrname = None
    
    title_varnames = (
        'name',
    )
    
    heading_varnames = (
        'typename',
        'name'
    )
    
    default_title = "{name}"
    default_heading = "{typename}: {name}"
    
    def __init__(self, blog, name):
        BlogEntries.__init__(self, blog)
        self.name = self.sortkey = name
        if self.prefix:
            self.urlshort = "/{0}/{1}/".format(self.prefix, name)
        else:
            self.urlshort = "/{}/".format(name)
    
    @cached_property
    def prev_next_suffix(self):
        return self.name
    
    def _get_sourcetype_sources(self):
        if self.sourcetype_attrname:
            return sorted(getattr(self.blog, self.sourcetype_attrname), key=attrgetter('sortkey'), reverse=True)
        return BlogEntries._get_sourcetype_sources(self)


class EntryMixin(BlogConfigUser):
    """All entry mixins in extensions must subclass this class.
    """
    pass


class PageMixin(BlogConfigUser):
    """All page mixins in extensions must subclass this class.
    """
    pass


class BlogMixin(BlogConfigUser):
    """All blog mixins in extensions must subclass this class.
    """
    pass


class BlogExtensionMeta(BlogConfigUserMeta):
    """Metaclass to automatically detect mixins in extension modules.
    """
    
    def __init__(cls, name, bases, attrs):
        super(BlogExtensionMeta, cls).__init__(name, bases, attrs)
        # Auto-detect entry, page, and blog mixins in this class's module
        thismod = sys.modules[__name__]
        clsmod = sys.modules[cls.__module__]
        for etype in ('Entry', 'Page', 'Blog'):
            mixin_klass = getattr(thismod, '%sMixin' % etype)
            ext_mixin = first_subclass(clsmod, mixin_klass)
            if ext_mixin:
                setattr(cls, '%s_mixin' % etype.lower(), ext_mixin)


class BlogExtension(BlogConfigUser, metaclass=BlogExtensionMeta):
    """Base class for extension mechanism.
    """
    
    config_vars = dict(
        container_link_template='<a href="{urlshort}">{title}</a>',
        container_link_sep='',
    )
    
    def __init__(self, config):
        BlogConfigUser.__init__(self, config)
        
        # Register this extension in the appropriate places
        thismod = sys.modules[__name__]
        attr_tmpl = '{}_'
        mixin_tmpl = '{}_mixin'
        for etype in extension_types:
            # Check for methods that extend a known attribute
            if any(
                item for item in prefixed_items(dir(self), attr_tmpl.format(etype))
                if not item.endswith('mixin')
            ):
                extension_map[etype].append(self)
            # Check for extensions that declare mixins
            mixin = getattr(self, mixin_tmpl.format(etype), None)
            if mixin:
                mixin_klass = getattr(thismod, '%sMixin' % etype.capitalize())
                mixin.extension_type = etype
                extend_attributes(mixin)
                oldcls = extension_types[etype]
                if issubclass(oldcls, mixin_klass):
                    bases = (mixin,) + oldcls.__bases__
                else:
                    bases = (mixin, oldcls)
                extcls = wraps_class(oldcls)(type(oldcls)('Extended', bases, {}))
                extension_types[etype] = extcls
        
        # Allow for post-init processing in subclasses
        self.post_init()
    
    def post_init(self):
        pass
    
    def get_links(self, containers, reverse=False):
        """Return HTML links to containers.
        """
        return "{}{}".format(self.container_link_sep, newline).join(
            self.container_link_template.format(**c.link_attrs)
            for c in sorted(containers, key=attrgetter('sortkey'), reverse=reverse)
        )
