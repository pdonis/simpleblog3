#!/usr/bin/env python
"""
Module PAGINATE -- Simple Blog Pagination Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.decotools import cached_method
from plib.stdlib.iters import group_into
from plib.stdlib.strings import universal_newline

from simpleblog import BlogEntries
from simpleblog.extensions import BlogExtension


def num_pages(source, max_entries):
    """Return number of pages required to paginate source.
    """
    q, r = divmod(len(source.entries), max_entries)
    return q + int(r > 0)


class PageEntries(BlogEntries):
    """Entries for a particular page of a paginated source.
    """
    
    config_vars = dict(
        page_max_entries=10,
        page_home_include_pagenum=False,
        page_title_template="{title} - Page {pagenum}",
        page_heading_template="{heading} - Page {pagenum}",
        page_prev_label="Newer Entries",
        page_next_label="Older Entries"
    )
    
    def __init__(self, blog, source, pagenum):
        BlogEntries.__init__(self, blog)
        self.orig_source = source
        self.pagenum = pagenum
        self.index_start = pagenum * self.page_max_entries
        self.index_end = self.index_start + self.page_max_entries
        self.urlshort = source.urlshort
        
        if (pagenum == 0) and not self.page_home_include_pagenum:
            self.default_title = source.title
            self.default_heading = source.heading
        else:
            page_attrs = dict(
                title=source.title,
                heading=source.heading,
                pagenum=pagenum + 1  # pagenum is zero-based
            )
            self.default_title = self.page_title_template.format(**page_attrs)
            self.default_heading = self.page_heading_template.format(**page_attrs)
    
    def _get_entries(self):
        return self.orig_source.entries[self.index_start:self.index_end]
    
    @cached_method
    def make_urlpath(self, urlshort, pagenum):
        if (pagenum != self.pagenum) and (pagenum == 0):
            return urlshort
        return "{}index{}".format(
            urlshort,
            pagenum if pagenum > 0 else ""
        )
    
    def _get_urlpath(self):
        if self.urlshort is not None:
            return self.make_urlpath(
                self.urlshort,
                self.pagenum
            )
        raise NotImplementedError
    
    @cached_method
    def make_pagelinks(self, format):
        linkspecs = (
            (0, -1, self.page_prev_label),
            (num_pages(self.orig_source, self.page_max_entries) - 1, 1, self.page_next_label)
        )
        return "{}{}".format(
            "&nbsp;&nbsp;".join([
                '<a href="{}{}">{}</a>'.format(
                    self.make_urlpath(self.urlshort, self.pagenum + ofs),
                    ".{}".format(format) if (self.pagenum + ofs) > 0 else "",
                    label
                ) for test, ofs, label in linkspecs
                if self.pagenum * ofs < test
            ]),
            universal_newline
        )


class PaginateExtension(BlogExtension):
    """Paginate all blog sources with multiple entries.
    """
    
    config_vars = dict(
        paginate_formats=dict(
            vartype=set,
            default=["html"]),
        page_max_entries=10,
        page_force_short=True
    )
    
    def page_mod_entry_params(self, page, params, entry):
        if self.page_force_short:
            try:
                pagenum = page.source.pagenum
            except AttributeError:
                pass
            else:
                if pagenum > 0:
                    params.update(
                        force_short=True
                    )
        return params
    
    def page_mod_attrs(self, page, attrs):
        attrs.update(
            page_links=(
                page.source.make_pagelinks(page.format)
                if isinstance(page.source, PageEntries)
                else ""
            )
        )
        return attrs
    
    def paginate(self, source, format):
        return (
            format in self.paginate_formats
            and isinstance(source, BlogEntries)
            and (len(source.entries) > self.page_max_entries)
        )
    
    def blog_mod_sources(self, blog, sources):
        newsources = []
        for source, format in sources:
            if self.paginate(source, format):
                newsources.extend(
                    (PageEntries(blog, source, pagenum), format)
                    for pagenum in xrange(num_pages(source, self.page_max_entries))
                )
            else:
                newsources.append((source, format))
        return newsources
