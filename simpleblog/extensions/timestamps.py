#!/usr/bin/env python
"""
Module TIMESTAMPS -- Simple Blog Timestamps Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from datetime import datetime

from simpleblog import BlogMixin, extendable_property, extendable_method
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension


timestamps_file = BlogExtension.config.get('timestamps_file', "timestamps")

timestamp_cache_format = "%Y-%m-%d %H:%M"


class TimestampEntryMixin(BlogMixin):
    
    @extendable_method()
    def string_from_datetime(self, dt, fmt):
        return dt.strftime(fmt)
    
    @extendable_property(
        cached(timestamps_file, reverse=True)
    )
    def timestamp_str(self):
        dt = self.datetime_from_mtime(self.mtime)
        return self.string_from_datetime(dt, timestamp_cache_format)
    
    @extendable_method()
    def datetime_from_string(self, s, fmt):
        return datetime.strptime(s, fmt)


class TimestampsExtension(BlogExtension):
    """Cache entry timestamps.
    """
    
    entry_mixin = TimestampEntryMixin
    
    def entry_get_timestamp(self, entry):
        return entry.datetime_from_string(entry.timestamp_str, timestamp_cache_format)
