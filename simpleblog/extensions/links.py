#!/usr/bin/env python
"""
Module LINKS -- Simple Blog Entry Links Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from itertools import groupby
from operator import itemgetter

from plib.stdlib.decotools import cached_property, cached_method
from plib.stdlib.strings import universal_newline

from simpleblog import BlogMixin, extendable_method
from simpleblog.extensions import BlogExtension


class LinksEntryMixin(BlogMixin):
    
    config_vars = dict(
        entrylink_sep="&nbsp;",
        link_next_template="next in {}",
        link_prev_template="previous in {}",
        link_display_sourcetypes=dict(
            vartype=set,
            default=['entry'])
    )
    
    @cached_property
    def entrylinks_template(self):
        return self.template_data("entry", "links")
    
    @cached_method
    def get_entrylink(self, attr, format, prefix):
        entry, label = attr
        title = (
            self.link_next_template,
            self.link_prev_template
        )[prefix.startswith('p')].format(label)
        if entry is not None:
            href = entry.make_permalink(format)
            return '<a href="{0}">{1}</a>'.format(href, title)
        return title
    
    @extendable_method()
    def prev_next_link(self, attr, format, prefix):
        if isinstance(attr, list):
            sep = '{0}{1}{0}'.format(universal_newline, self.entrylink_sep)
            return sep.join(
                self.get_entrylink(value, format, prefix)
                for value in attr
            )
        return self.get_entrylink(attr, format, prefix)
    
    @extendable_method()
    def prev_next_attrs(self, format):
        prefixes = ('next_in_', 'prev_in_')
        return dict(
            (attrname, self.prev_next_link(
                getattr(self, attrname), format, prefix
            ))
            for prefix in prefixes
            for attrname in dir(self)
            if attrname.startswith(prefix)
        )
    
    @cached_method
    def make_entrylinks(self, format, params):
        if params.sourcetype in self.link_display_sourcetypes:
            return self.entrylinks_template.format(**self.prev_next_attrs(format))
        return ""


class LinksExtension(BlogExtension):
    """Add links to previous and next entries in containers.
    """
    
    config_vars = dict(
        link_sourcetypes=dict(
            blog=None
        )
    )
    
    entry_mixin = LinksEntryMixin
    
    def entry_mod_attrs(self, entry, attrs, format, params):
        attrs.update(
            entrylinks=entry.make_entrylinks(format, params)
        )
        return attrs
    
    def page_mod_entry_params(self, page, params, entry):
        params.update(
            sourcetype=page.source.sourcetype
        )
        return params
    
    def blog_mod_sources(self, blog, sources):
        prev_tmpl = 'prev_in_{}'
        next_tmpl = 'next_in_{}'
        
        # Set up previous/next links within each source
        multisources = set()
        for source, _ in groupby(sources, itemgetter(0)):
            sourcetype = source.sourcetype
            if sourcetype in self.link_sourcetypes:
                if source.multisource:
                    multisources.add(source.multisource)
                propname = self.link_sourcetypes[sourcetype]
                prop = getattr(source, propname) if propname else None
                entries = source.entries
                for index, entry in enumerate(entries):
                    prev_attr = (
                        entries[index - 1]
                        if index > 0 else None,
                        prop or sourcetype
                    )
                    next_attr = (
                        entries[index + 1]
                        if index < (len(entries) - 1) else None,
                        prop or sourcetype
                    )
                    if source.entry_sort_reversed:
                        prev_attr, next_attr = next_attr, prev_attr
                    if not source.multisource:
                        setattr(entry, prev_tmpl.format(sourcetype), prev_attr)
                        setattr(entry, next_tmpl.format(sourcetype), next_attr)
                    if prop:
                        setattr(entry, prev_tmpl.format(prop), prev_attr)
                        setattr(entry, next_tmpl.format(prop), next_attr)
        
        # Add previous/next link collections for multisources
        for entry in blog.all_entries:
            for attrname in multisources:
                names = sorted(getattr(entry, attrname))
                if names:
                    setattr(entry, prev_tmpl.format(attrname), [
                        getattr(entry, prev_tmpl.format(name))
                        for name in names
                    ])
                    setattr(entry, next_tmpl.format(attrname), [
                        getattr(entry, next_tmpl.format(name))
                        for name in names
                    ])
        
        return sources
