#!/usr/bin/env python
"""
Module FEED -- Simple Blog Feed Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import re
import time as _time
from datetime import tzinfo, timedelta, datetime

from plib.stdlib.decotools import cached_property

from simpleblog import (extendable_property,
    html_newline,
    weekdaynames, monthnames)
from simpleblog.extensions import BlogExtension


# TZINFO code cribbed from Python docs for datetime module

ZERO = timedelta(0)
HOUR = timedelta(hours=1)


class UTC(tzinfo):
    
    def utcoffset(self, dt):
        return ZERO
    
    def tzname(self, dt):
        return "UTC"
    
    def dst(self, dt):
        return ZERO


STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0


tz_utc = UTC()

tz_local = LocalTimezone()


template_rss20 = "{0}, {1.day:02d} {2} {1.year} {1.hour:02d}:{1.minute:02d} GMT"

template_atom = "{0.year}-{0.month:02d}-{0.day:02d}T{0.hour:02d}:{0.minute:02d}:00Z"


class FeedEntryMixin(object):
    
    @cached_property
    def timestamp_utc(self):
        t = self.timestamp
        t_local = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo=tz_local)
        return t_local.astimezone(tz_utc)
    
    @extendable_property()
    def timestamp_atom(self):
        t = self.timestamp_utc
        return template_atom.format(t)
    
    @extendable_property()
    def timestamp_rss20(self):
        t = self.timestamp_utc
        weekday = weekdaynames[t.weekday()]
        monthname = monthnames[t.month]
        return template_rss20.format(weekday, t, monthname)


class FeedBlogMixin(object):
    
    @extendable_property()
    def feed_formats(self):
        return set(["rss20", "atom"]).intersection(self.index_formats)


re_link = re.compile(r'<a href=\"\/([A-Za-z0-9\-\/\.]+)\"')


def fixup_relative_links(html, root_url):
    """Convert relative links in HTML to absolute links based on root URL.
    """
    return re.sub(
        re_link,
        lambda m: '<a href="{0}/{1}"'.format(root_url, m.group(1)),
        html
    )


feedlink_template_rss20 = """<link rel="alternate" type="application/rss+xml" title="RSS 2.0"
      href="{rss20_url}">"""

feedlink_template_atom = """<link rel="alternate" type="application/atom+xml" title="Atom"
      href="{atom_url}">"""


class FeedExtension(BlogExtension):
    """Add RSS and Atom feed links to home page.
    """
    
    entry_mixin = FeedEntryMixin
    blog_mixin = FeedBlogMixin
    
    def entry_mod_body(self, entry, body, format, params):
        if format in entry.blog.feed_formats:
            return fixup_relative_links(body, entry.blog.metadata['root_url'])
        return body
    
    def entry_mod_attrs(self, entry, attrs, format, params):
        do_rss20 = 'rss20' in entry.blog.feed_formats
        do_atom = 'atom' in entry.blog.feed_formats
        if do_rss20 or do_atom:
            attrs.update(
                root_url=entry.blog.metadata['root_url'],
                author=entry.blog.metadata['author'],
                email=entry.blog.metadata['email']
            )
            if do_rss20:
                attrs.update(
                    timestamp_rss20=entry.timestamp_rss20
                )
            if do_atom:
                attrs.update(
                    timestamp_atom=entry.timestamp_atom
                )
        return attrs
    
    def page_mod_attrs(self, page, attrs):
        if 'atom' in page.blog.feed_formats:
            attrs.update(
                sys_timestamp_atom=template_atom.format(datetime.utcnow())
            )
        if 'rss20' in page.blog.feed_formats:
            language = page.blog.metadata['language']
            try:
                country = page.blog.metadata['country'].lower()
            except KeyError:
                pass
            else:
                language = '-'.join([language, country])
            attrs.update(
                blog_language_rss20=language
            )
        return attrs
    
    def blog_mod_required_metadata(self, blog, data):
        if 'rss20' in blog.feed_formats:
            data.add('language')
        return data
    
    def blog_mod_default_metadata(self, blog, data):
        if 'rss20' in blog.feed_formats:
            data.update(
                rss20_url="/index.rss20"
            )
        if 'atom' in blog.index_formats:
            data.update(
                atom_url="/index.atom",
            )
        return data
    
    def blog_mod_sources(self, blog, sources):
        feedlinks = []
        if 'rss20' in blog.feed_formats:
            feedlinks.append(
                feedlink_template_rss20.format(**blog.metadata)
            )
        if 'atom' in blog.feed_formats:
            feedlinks.append(
                feedlink_template_atom.format(**blog.metadata)
            )
        blog.metadata['feed_links'] = html_newline.join(feedlinks)
        return sources
