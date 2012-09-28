#!/usr/bin/env python
"""
Module TIMESTAMPS -- Simple Blog Timestamps Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from datetime import datetime
from functools import total_ordering

from plib.stdlib.decotools import convert

from simpleblog import BlogConfigUser, BlogMixin, extendable_property
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension


@total_ordering
class Timestamp(BlogConfigUser):
    """Blog entry time stamp.
    
    Wraps ``datetime.datetime`` to customize for usage here. Note that
    we use "naive" ``datetime`` objects; we don't expect blog entry
    times to be close enough to make correct handling of time zones,
    DST transitions, etc. to be an issue. However, if you want to ensure
    that such issues won't arise, you can set the ``utc_timestamps``
    config to use UTC timestamps instead of platform local time. Also,
    timestamps are normally cached only to the minute; if you want to
    cache them to the second, set the ``timestamps_cache_seconds``
    config.
    """
    
    config_vars = dict(
        utc_timestamps=False,
        timestamp_cache_format="%Y-%m-%d-%H-%M"
    )
    
    datetime_attrs = (
        'year', 'month', 'day',
        'hour', 'minute', 'second',
        'weekday'
    )
    
    def __init__(self, data):
        # A hack but it works...
        self.config = BlogExtension.config
        
        if isinstance(data, datetime):
            # It's a datetime object computed from the file mtime
            self._datetime = data
        elif isinstance(data, basestring):
            # It's a string timestamp from the cache
            self._datetime = datetime.strptime(data, self.timestamp_cache_format)
        else:
            raise ValueError("{!r} is not a valid entry timestamp".format(data))
        for attr in self.datetime_attrs:
            setattr(self, attr, getattr(self._datetime, attr))
    
    def __repr__(self):
        return "Timestamp: {!r}".format(self._datetime)
    
    def __str__(self):
        return self._datetime.strftime(self.timestamp_cache_format)
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._datetime == other._datetime
        if isinstance(other, datetime):
            return self._datetime == other
        raise NotImplementedError
    
    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self._datetime > other._datetime
        if isinstance(other, datetime):
            return self._datetime > other
        raise NotImplementedError


timestamps_file = BlogExtension.config.get('timestamps_file', "timestamps")


class TimestampEntryMixin(BlogMixin):
    
    @extendable_property(
        cached(timestamps_file, reverse=True, objtype=Timestamp)
    )
    def timestamp(self):
        return self.datetime_from_mtime


class TimestampsExtension(BlogExtension):
    """Cache entry timestamps.
    """
    
    entry_mixin = TimestampEntryMixin
