#!/usr/bin/env python
"""
Module ARCHIVES -- Simple Blog Archives Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from collections import defaultdict

from plib.stdlib.decotools import cached_property
from plib.stdlib.localize import monthname, monthname_long

from simpleblog import BlogEntries
from simpleblog.extensions import BlogExtension, get_links


year_entries = defaultdict(list)
month_entries = defaultdict(list)
day_entries = defaultdict(list)


class BlogArchiveEntries(BlogEntries):
    """Archive of entries spanning a given time period.
    """
    
    config_vars = dict(
        prefix=('archives_prefix', ""),
        archive_use_monthnames=False,
        archive_long_monthnames=False,
        archive_year_template="{year}",
        archive_month_template="{year}-{monthkey}",
        archive_day_template="{year}-{monthkey}-{day}"
    )
    
    sourcetype = 'archive'
    
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
                title_template = self.archive_day_template
            else:
                self.sortkey = (year, month)
                self.urlshort = "/{0}/{1}/".format(year, monthkey)
                title_template = self.archive_month_template
        else:
            self.sortkey = (year,)
            self.urlshort = "/{}/".format(year)
            title_template = self.archive_year_template
        
        if self.prefix:
            self.urlshort = "/{0}{1}".format(self.prefix, self.urlshort)
        
        self.title = title_template.format(**vars(self))
        self.heading = "Archive: {}".format(self.title)
    
    def _get_entries(self):
        if self.month:
            if self.day:
                return day_entries[(self.year, self.month, self.day)]
            return month_entries[(self.year, self.month)]
        return year_entries[self.year]


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
        
        def archive_containers(t):
            if self.archive_years:
                yield year_entries[t.year]
            if self.archive_months:
                yield month_entries[(t.year, t.month)]
            if self.archive_days:
                yield day_entries[(t.year, t.month, t.day)]
        
        for entry in blog.all_entries:
            for container in archive_containers(entry.timestamp):
                container.append(entry)
        
        blog.all_archives = []
        archive_links = []
        
        if self.archive_years:
            years = [
                BlogArchiveEntries(blog, year)
                for year in year_entries
            ]
            blog.all_archives.extend(years)
            if self.archive_link_years:
                archive_links.extend(years)
        
        if self.archive_months:
            months = [
                BlogArchiveEntries(blog, year, month)
                for year, month in month_entries
            ]
            blog.all_archives.extend(months)
            if self.archive_link_months:
                archive_links.extend(months)
        
        if self.archive_days:
            days = [
                BlogArchiveEntries(blog, year, month, day)
                for year, month, day in day_entries
            ]
            blog.all_archives.extend(days)
            if self.archive_link_days:
                archive_links.extend(days)
        
        blog.metadata['archive_links'] = get_links(archive_links, True)
        
        sources.extend(
            (archive, "html")
            for archive in blog.all_archives
        )
        
        return sources
