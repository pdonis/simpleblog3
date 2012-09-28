#!/usr/bin/env python
"""
Module FEED -- Simple Blog Feed Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import re
from datetime import datetime
from itertools import groupby

from plib.stdlib.decotools import cached_property, cached_method
from plib.stdlib.localize import weekdayname, monthname, monthname_long
from plib.stdlib.strings import universal_newline
from plib.stdlib.tztools import UTCTimezone, LocalTimezone

from simpleblog import BlogMixin, extendable_property, BlogEntries
from simpleblog.extensions import BlogExtension


tz_utc = UTCTimezone()

tz_local = LocalTimezone()


archive_marker = "<fh:archive />"

archive_current_tmpl = '<link rel="current" href="{}/index.{}" />'

archive_rel_tmpl = """<link rel="{}-archive" href="{}{}{}.{}" />"""

archive_rel_specs = ('prev', 'next')


class BlogCurrentFeedEntries(BlogEntries):
    """Current syndication feed entries.
    """
    
    config_vars = dict(
        archive_use_monthnames=False,
        archive_long_monthnames=False,
        archive_feed_dirs=False
    )
    
    urlshort = "/"
    
    is_current_feed = True
    
    def __init__(self, blog, arglist, *args):
        BlogEntries.__init__(self, blog)
        self.arglist = arglist
        self.args = args
        self.argindex = i = arglist.index(args)
        
        assert self.is_current_feed == (i == (len(arglist) - 1))
        
        self.prev_args = arglist[i - 1] if i > 0 else None
        self.next_args = arglist[i + 1] if i < (len(arglist) - 2) else None
        
        self.title = self.argstr('-', *args)
        self.heading = "Feed Archive: {}".format(self.title)
    
    @cached_method
    def argstr(self, sep, *args):
        if (len(args) > 1) and self.archive_use_monthnames:
            arg1 = (
                monthname_long(args[1]) if self.archive_long_monthnames
                else monthname(args[1])
            )
            args = (args[0], arg1) + args[2:]
        return sep.join(
            str(arg).rjust(2, '0') for arg in args
        )
    
    @cached_method
    def entry_match(self, entry):
        t = entry.timestamp
        return (t.year, t.month, t.day)[:len(self.args)] == self.args
    
    def _get_entries(self):
        for entry in self.blog.all_entries:
            if self.entry_match(entry):
                yield entry
    
    @cached_method
    def args_urlshort(self, *args):
        if self.archive_feed_dirs:
            sep = suffix = '/'
        else:
            sep = '-'
            suffix = ''
        return "/{}{}".format(self.argstr(sep, *args), suffix)
    
    @cached_property
    def archive_elem(self):
        return "" if self.is_current_feed else archive_marker
    
    @cached_method
    def archive_current(self, format):
        return archive_current_tmpl.format(
            self.blog.metadata['root_url'],
            format
        ) if not self.is_current_feed else ""
    
    @cached_method
    def archive_rel(self, rel, format):
        args = getattr(self, '{}_args'.format(rel), None)
        if args:
            return archive_rel_tmpl.format(
                rel,
                self.blog.metadata['root_url'],
                self.args_urlshort(*args),
                "index" if self.archive_feed_dirs else "",
                format
            )
        return ""
    
    @cached_method
    def archive_elements(self, format):
        return "{}{}{}".format(
            universal_newline,
            universal_newline.join(
                item for item in [
                    self.archive_elem,
                    self.archive_current(format)
                ] + [
                    self.archive_rel(rel, format)
                    for rel in archive_rel_specs
                ]
                if item
            ),
            universal_newline
        )


class BlogArchiveFeedEntries(BlogCurrentFeedEntries):
    """Feed archive entries.
    """
    
    is_current_feed = False
    
    @cached_property
    def urlshort(self):
        return self.args_urlshort(*self.args)
    
    def _get_urlpath(self):
        if (not self.archive_feed_dirs) and (self.urlshort is not None):
            return self.urlshort
        return super(BlogArchiveFeedEntries, self)._get_urlpath()


template_rss = "{0}, {1.day:02d} {2} {1.year} {1.hour:02d}:{1.minute:02d} GMT"

template_atom = "{0.year}-{0.month:02d}-{0.day:02d}T{0.hour:02d}:{0.minute:02d}:00Z"


def rss_format(t):
    return template_rss.format(
        weekdayname(t.weekday(), dt=True),
        t,
        monthname(t.month)
    )


def atom_format(t):
    return template_atom.format(t)


class FeedEntryMixin(BlogMixin):
    
    config_vars = dict(
        utc_timestamps=False
    )
    
    @extendable_property()
    def timestamp_utc(self):
        t = self.timestamp
        if self.utc_timestamps:
            return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, tzinfo=tz_utc)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, tzinfo=tz_local).astimezone(tz_utc)
    
    @extendable_property()
    def timestamp_atom(self):
        return atom_format(self.timestamp_utc)
    
    @extendable_property()
    def timestamp_rss(self):
        return rss_format(self.timestamp_utc)


known_feed_formats = ["rss", "atom"]

known_archive_feed_formats = ["atom"]


class FeedBlogMixin(BlogMixin):
    
    @extendable_property()
    def feed_formats(self):
        return set(known_feed_formats).intersection(self.index_formats)
    
    @extendable_property()
    def archive_feed_formats(self):
        return set(known_archive_feed_formats).intersection(self.index_formats)
    
    @cached_property
    def feedlink_template_rss(self):
        return self.template_data("link", "rss")
    
    @cached_property
    def feedlink_template_atom(self):
        return self.template_data("link", "atom")


re_link = re.compile(r'<a href=\"\/([A-Za-z0-9\-\/\.]+)\"')


def fixup_relative_links(html, root_url):
    """Convert relative links in HTML to absolute links based on root URL.
    """
    return re.sub(
        re_link,
        lambda m: '<a href="{0}/{1}"'.format(root_url, m.group(1)),
        html
    )


class FeedExtension(BlogExtension):
    """Add RSS and Atom feed links to home page.
    """
    
    config_vars = dict(
        archive_feeds=None
    )
    
    entry_mixin = FeedEntryMixin
    blog_mixin = FeedBlogMixin
    
    def entry_mod_body(self, entry, body, format, params):
        if format in entry.blog.feed_formats:
            return fixup_relative_links(body, entry.blog.metadata['root_url'])
        return body
    
    def entry_mod_attrs(self, entry, attrs, format, params):
        do_rss = 'rss' in entry.blog.feed_formats
        do_atom = 'atom' in entry.blog.feed_formats
        if do_rss or do_atom:
            attrs.update(
                root_url=entry.blog.metadata['root_url'],
                author=entry.blog.metadata['author'],
                email=entry.blog.metadata['email']
            )
            if do_rss:
                attrs.update(
                    timestamp_rss=entry.timestamp_rss
                )
            if do_atom:
                attrs.update(
                    timestamp_atom=entry.timestamp_atom
                )
        return attrs
    
    def page_mod_attrs(self, page, attrs):
        if page.format in page.blog.feed_formats:
            t = max(entry.timestamp_utc for entry in page.entries)
            if page.format in page.blog.archive_feed_formats:
                attrs.update(
                    page_archive_elements=page.source.archive_elements(
                        page.format
                    ) if self.archive_feeds else ""
                )
            if page.format == 'atom':
                attrs.update(
                    page_timestamp_atom=atom_format(t)
                )
            if page.format == 'rss':
                language = page.blog.metadata['language']
                try:
                    country = page.blog.metadata['country'].lower()
                except KeyError:
                    pass
                else:
                    language = '-'.join([language, country])
                attrs.update(
                    page_timestamp_rss=rss_format(t),
                    blog_language_rss=language
                )
        return attrs
    
    def blog_mod_required_metadata(self, blog, data):
        if 'rss' in blog.feed_formats:
            data.add('language')
        return data
    
    def blog_mod_default_metadata(self, blog, data):
        if 'rss' in blog.feed_formats:
            data.update(
                rss_title="RSS",
                rss_url="/index.rss"
            )
        if 'atom' in blog.feed_formats:
            data.update(
                atom_title="Atom",
                atom_url="/index.atom",
            )
        return data
    
    @cached_method
    def archive_feed_args(self, blog):
        eattrs = ('year', 'month', 'day')
        eattrs = eattrs[:eattrs.index(self.archive_feeds) + 1]
        return [
            groupkey for groupkey, _ in groupby(
                sorted(e.timestamp for e in blog.all_entries),
                lambda t: tuple(
                    getattr(t, attrname) for attrname in eattrs
                )
            )
        ]
    
    @cached_method
    def current_feed_entries(self, blog):
        arglist = self.archive_feed_args(blog)
        return BlogCurrentFeedEntries(blog, arglist, *arglist[-1])
    
    @cached_method
    def archive_feed_entries(self, blog, *args):
        arglist = self.archive_feed_args(blog)
        return BlogArchiveFeedEntries(blog, arglist, *args)
    
    def blog_mod_index_entries(self, blog, entries, format):
        if self.archive_feeds and (format in blog.archive_feed_formats):
            return self.current_feed_entries(blog)
        return entries
    
    def blog_mod_sources(self, blog, sources):
        
        feedlinks = []
        if 'rss' in blog.feed_formats:
            feedlinks.append(
                blog.feedlink_template_rss.format(**blog.metadata)
            )
        if 'atom' in blog.feed_formats:
            feedlinks.append(
                blog.feedlink_template_atom.format(**blog.metadata)
            )
        blog.metadata['feed_links'] = universal_newline.join(feedlinks)
        
        if self.archive_feeds:
            arglist = self.archive_feed_args(blog)
            sources.extend(
                (self.archive_feed_entries(blog, *args), format)
                for args in arglist[:-1]
                for format in blog.archive_feed_formats
            )
        
        return sources
