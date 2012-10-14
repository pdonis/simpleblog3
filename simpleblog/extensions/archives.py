#!/usr/bin/env python
"""
Module ARCHIVES -- Simple Blog Archives Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from collections import defaultdict
from operator import attrgetter

from plib.stdlib.decotools import cached_property
from plib.stdlib.localize import monthname, monthname_long

from simpleblog import BlogEntries
from simpleblog.extensions import BlogExtension


class BlogArchiveEntries(BlogEntries):
    """Archive of entries spanning a given time period.
    """
    
    config_vars = dict(
        prefix=('archives_prefix', ""),
        archive_use_monthnames=False,
        archive_long_monthnames=False,
        archive_year_template=u"{year}",
        archive_month_template=u"{year}-{monthkey}",
        archive_day_template=u"{year}-{monthkey}-{day}"
    )
    
    sourcetype = 'archive'
    
    title_varnames = (
        'year',
        'month',
        'day',
        'monthkey'
    )
    
    heading_varnames = (
        'title',
    )
    
    default_heading = u"Archive: {title}"
    
    def __init__(self, blog, year, month=0, day=0):
        BlogEntries.__init__(self, blog)
        self.year = year
        self.month = month
        if month:
            self.monthname = mname = monthname(month)
            self.monthname_long = mname_long = monthname_long(month)
            self.monthkey = monthkey = (
                "{:02d}".format(month) if not self.archive_use_monthnames else
                mname if not self.archive_long_monthnames else
                mname_long
            )
        else:
            self.monthname = self.monthname_long = self.monthkey = ""
        self.day = day
        
        if month:
            if day:
                self.sortkey = (year, month, day)
                self.urlshort = "/{0}/{1}/{2:02d}/".format(year, monthkey, day)
                self.default_title = self.archive_day_template
            else:
                self.sortkey = (year, month)
                self.urlshort = "/{0}/{1}/".format(year, monthkey)
                self.default_title = self.archive_month_template
        else:
            self.sortkey = (year,)
            self.urlshort = "/{}/".format(year)
            self.default_title = self.archive_year_template
        
        if self.prefix:
            self.urlshort = "/{0}{1}".format(self.prefix, self.urlshort)
    
    def _get_entries(self):
        if self.month:
            if self.day:
                return self.blog.day_entries[(self.year, self.month, self.day)]
            return self.blog.month_entries[(self.year, self.month)]
        return self.blog.year_entries[self.year]
    
    def _get_sourcetype_sources(self):
        archives = self.blog.all_archives
        if self.month:
            if self.day:
                match = lambda a: (a.year == self.year) and (a.month == self.month)
            else:
                match = lambda a: (a.year == self.year) and (a.day == 0)
        else:
            match = lambda a: (a.month == 0) and (a.day == 0)
        return sorted((a for a in archives if match(a)), key=attrgetter('sortkey'))


class ArchivesExtension(BlogExtension):
    """Add blog archive pages.
    """
    
    config_vars = dict(
        archive_years=False,
        archive_months=False,
        archive_days=False,
        archive_link_years=False,
        archive_link_months=False,
        archive_link_days=False
    )
    
    def blog_mod_sources(self, blog, sources):
        
        blog.year_entries = defaultdict(list)
        blog.month_entries = defaultdict(list)
        blog.day_entries = defaultdict(list)
        
        def archive_containers(t):
            if self.archive_years:
                yield blog.year_entries[t.year]
            if self.archive_months:
                yield blog.month_entries[(t.year, t.month)]
            if self.archive_days:
                yield blog.day_entries[(t.year, t.month, t.day)]
        
        for entry in blog.all_entries:
            for container in archive_containers(entry.timestamp):
                container.append(entry)
        
        blog.all_archives = []
        archive_links = []
        
        if self.archive_years:
            years = [
                BlogArchiveEntries(blog, year)
                for year in blog.year_entries
            ]
            blog.all_archives.extend(years)
            if self.archive_link_years:
                archive_links.extend(years)
        
        if self.archive_months:
            months = [
                BlogArchiveEntries(blog, year, month)
                for year, month in blog.month_entries
            ]
            blog.all_archives.extend(months)
            if self.archive_link_months:
                archive_links.extend(months)
        
        if self.archive_days:
            days = [
                BlogArchiveEntries(blog, year, month, day)
                for year, month, day in blog.day_entries
            ]
            blog.all_archives.extend(days)
            if self.archive_link_days:
                archive_links.extend(days)
        
        blog.metadata.update(
            archive_links=self.get_links(archive_links, True)
        )
        
        sources.extend(
            (archive, "html")
            for archive in blog.all_archives
        )
        
        return sources
