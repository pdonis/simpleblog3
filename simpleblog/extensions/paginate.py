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

from simpleblog import BlogEntries, noresult, newline
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
        page_title_template=u"{title} - Page {pagenum}",
        page_heading_template=u"{heading} - Page {pagenum}",
        page_newer_label=u"Newer Entries",
        page_older_label=u"Older Entries",
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
            (0, -1, self.page_newer_label),
            (num_pages(self.orig_source, self.page_max_entries) - 1, 1, self.page_older_label)
        )
        return tuple(
            u'<a href="{}{}">{}</a>'.format(
                self.make_urlpath(self.urlshort, self.pagenum + ofs),
                ".{}".format(format) if (self.pagenum + ofs) > 0 else "",
                label
            ) if (self.pagenum * ofs) < test else ""
            for test, ofs, label in linkspecs
        )


class PaginateExtension(BlogExtension):
    """Paginate all blog sources with multiple entries.
    """
    
    config_vars = dict(
        paginate_formats=dict(
            vartype=set,
            default=["html"]),
        page_max_entries=10,
        page_force_short=True,
        page_links_include_sources=False,
        page_link_sep=u"&nbsp;&nbsp;"
    )
    
    def page_get_link_source(self, page):
        if isinstance(page.source, PageEntries):
            return page.source.orig_source
        return noresult
    
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
        if isinstance(page.source, PageEntries):
            page_link_newer, page_link_older = page.source.make_pagelinks(page.format)
        else:
            page_link_newer = page_link_older = ""
        if self.page_links_include_sources:
            links = (
                attrs['page_sourcelink_next'],
                page_link_newer,
                page_link_older,
                attrs['page_sourcelink_prev']
            )
        else:
            links = (page_link_newer, page_link_older)
        page_links = self.page_link_sep.join(link for link in links if link)
        attrs.update(
            page_links="{}{}".format(page_links, newline) if page_links else "",
            page_link_newer=page_link_newer,
            page_link_older=page_link_older
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
