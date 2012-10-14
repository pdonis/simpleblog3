#!/usr/bin/env python
"""
Module INDEXES -- Simple Blog Index Generator Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from operator import attrgetter

from plib.stdlib.decotools import cached_property

from simpleblog import BlogObject, BlogPage, prefixed_keys, newline
from simpleblog.extensions import BlogExtension


class BlogIndexPage(BlogPage):
    """Specialized page class for page with links instead of entries.
    """
    
    config_vars = dict(
        index_link_template=u"{link}",
        index_link_suffix_template=u"",
        link_index_title_template=u"{heading}",
        link_index_heading_template=u"{label} Index",
        link_index_heading_alpha=u"Alphabetical",
        link_index_heading_chrono=u"Chronological",
        link_index_heading_key=u"Key",
        link_index_sep=u"<br>"
    )
    
    def __init__(self, blog, format, alpha):
        BlogObject.__init__(self, blog)
        self.source = self.entries = None
        self.format = format
        self.alpha = alpha
        self.urlpath = "/index-{0}.{1}".format(
            "key" if alpha is None else "alpha" if alpha else "chrono",
            format
        )
        self.heading = self.link_index_heading_template.format(
            label=(
                self.link_index_heading_key if alpha is None
                else self.link_index_heading_alpha if alpha
                else self.link_index_heading_chrono
            )
        )
        self.title = self.link_index_title_template.format(
            heading=self.heading
        )
    
    @cached_property
    def indexlinks_template(self):
        return self.template_data("index", "links")
    
    @cached_property
    def no_entries(self):
        # Hack to populate the page with links instead of entries
        if self.alpha is None:
            key = label = attrgetter('cachekey')
            suffix = lambda entry: ""
            reverse = False
        else:
            label = attrgetter('title')
            key = label if self.alpha else attrgetter('timestamp')
            suffix = lambda entry: self.index_link_suffix_template.format(entry)
            reverse = not self.alpha
        return self.indexlinks_template.format(
            index_links=("{}{}".format(self.link_index_sep, newline)).join([
                self.index_link_template.format(
                    link=u'<a href="{0}.{1}">{2}</a>{3}'.format(
                        entry.urlpath, self.format, label(entry), suffix(entry)
                    )
                ) for entry in sorted(self.blog.all_entries, key=key, reverse=reverse)
            ])
        )


class IndexesExtension(BlogExtension):
    """Add alphabetical and/or chronological link index pages to blog.
    """
    
    config_vars = dict(
        link_index_alpha=False,
        link_index_chrono=True,
        link_index_key=False,
        link_index_formats=dict(
            vartype=set,
            default=["html"])
    )
    
    @cached_property
    def link_index_alphas(self):
        result = []
        if self.link_index_key:
            result.append(None)
        if self.link_index_chrono:
            result.append(False)
        if self.link_index_alpha:
            result.append(True)
        return result
    
    def blog_mod_pages(self, blog, pages):
        pages.extend(
            BlogIndexPage(blog, format, alpha)
            for format in self.link_index_formats
            for alpha in self.link_index_alphas
        )
        return pages
