#!/usr/bin/env python
"""
Module CATEGORIES -- Simple Blog Categories Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os

from plib.stdlib.decotools import cached_property
from plib.stdlib.ostools import subdirs

from simpleblog.extensions import (BlogExtension,
    NamedEntries, get_links)


class BlogCategory(NamedEntries):
    """Category of blog entries.
    """
    
    sourcetype = 'category'
    typename = "Category"
    
    @cached_property
    def prefix(self):
        return self.config.get('categories_prefix', "")
    
    def _get_entries(self):
        return [
            e for e in self.blog.all_entries if e.category == self.name
        ]


def make_category_link(category):
    return '<a href="/{0}/" title="Category">{0}</a>'.format(category)


class CategoryExtension(BlogExtension):
    """Add category to entry and category pages to blog.
    """
    
    def entry_post_init(self, entry):
        # The category will be an empty string for entries in
        # the root entries dir instead of a subdir
        entry.category, entry.name = os.path.split(entry.name)
        
        if entry.category:
            link = make_category_link(entry.category)
        else:
            link = "(None)"
        entry.metadata.update(
            categorylink=link
        )
    
    def entry_mod_attrs(self, entry, attrs, format, params):
        attrs.update(
            category=entry.category
        )
        return attrs
    
    def blog_mod_all_entries(self, blog, all_entries):
        # Entries can now live in subdirs of entries_dir (each
        # subdir defines a category)
        return all_entries + [
            blog.entry_class(blog, os.path.join(subdir, name))
            for subdir in subdirs(blog.entries_dir)
            for name in blog.filter_entries(os.path.join(blog.entries_dir, subdir))
        ]
    
    def blog_mod_sources(self, blog, sources):
        
        blog.category_names = set(subdirs(blog.entries_dir))
        
        blog.all_categories = [
            BlogCategory(blog, catname)
            for catname in blog.category_names
        ]
        
        blog.metadata['category_links'] = get_links(blog.all_categories)
        
        sources.extend(
            (category, "html")
            for category in blog.all_categories
        )
        
        return sources
