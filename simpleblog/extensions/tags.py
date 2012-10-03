#!/usr/bin/env python
"""
Module TAGS -- Simple Blog Tags Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.decotools import cached_property, convert
from plib.stdlib.strings import split_string, universal_newline

from simpleblog import BlogMixin, extendable_property
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension, NamedEntries


tags_file = BlogExtension.config.get('tags_file', "tags")


def makelink(name, prefix=None):
    if prefix:
        href = "{0}/{1}".format(prefix, name)
    else:
        href = name
    return '<a href="/{0}/">{1}</a>'.format(href, name)


class Tagset(object):
    """Blog entry tag set.
    
    Wraps a set of blog tags to customize for usage here. The
    ``__str__`` method ensures that the tags can be written to
    and read back from the tag cache file, as well as from the
    tag string in the entry source file. Other important methods
    are delegated to the underlying set object.
    """
    
    def __init__(self, s):
        self._tags = frozenset(t.strip() for t in s.split(','))
    
    def __str__(self):
        return ','.join(sorted(self._tags))
    
    def __iter__(self):
        return iter(self._tags)
    
    def __contains__(self, v):
        return v in self._tags
    
    def __len__(self):
        return len(self._tags)


class BlogTag(NamedEntries):
    """Entries matching a given tag.
    """
    
    config_vars = dict(
        prefix=('tags_prefix', "")
    )
    
    sourcetype = 'tag'
    multisource = 'tags'
    typename = "Tag"
    
    def _get_entries(self):
        return [
            e for e in self.blog.all_entries if self.name in e.tags
        ]


class TagsEntryMixin(BlogMixin):
    
    config_vars = dict(
        tags_marker="#tags ",
        tags_end=universal_newline
    )
    
    def _do_load(self):
        raw = super(TagsEntryMixin, self)._do_load()
        pre, mid, post = split_string(raw,
            self.tags_marker, self.tags_end, find_newlines=False)
        if pre and post:
            self._tagstr = mid
            raw = ''.join([pre[:-len(self.tags_marker)], post[len(self.tags_end):]])
        else:
            self._tagstr = ""
        return raw
    
    @extendable_property(
        cached(tags_file, objtype=Tagset)
    )
    def tags(self):
        self.load()
        return self._tagstr


class TagsExtension(BlogExtension):
    """Add tags to entry and tag pages to blog.
    """
    
    config_vars = dict(
        tags_prefix=""
    )
    
    entry_mixin = TagsEntryMixin
    
    def entry_post_init(self, entry):
        entry.metadata.update(
            taglinks=',{}'.format(universal_newline).join(
                makelink(tag, self.tags_prefix) for tag in sorted(entry.tags)
            )
        )
    
    def entry_mod_attrs(self, entry, attrs, format, params):
        attrs.update(
            tags=str(entry.tags)
        )
        return attrs
    
    def blog_mod_sources(self, blog, sources):
        
        blog.tag_names = set(t
            for e in blog.all_entries
            for t in e.tags
        )
        
        blog.all_tags = [
            BlogTag(blog, tagname)
            for tagname in blog.tag_names
        ]
        
        blog.metadata.update(
            tag_links=self.get_links(blog.all_tags)
        )
        
        sources.extend(
            (tag, "html")
            for tag in blog.all_tags
        )
        
        return sources
