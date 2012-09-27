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

from simpleblog import BlogMixin, extendable_property
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension


@total_ordering
class Timestamp(object):
    """Blog entry time stamp.
    
    Wraps ``datetime.datetime`` to customize for usage here. Note that
    we use "naive" ``datetime`` objects; we don't expect blog entry
    times to be close enough to make correct handling of time zones,
    DST transitions, etc. to be an issue. This does, however, mean that
    "original" timestamps, generated from the entry source file mtime
    when the entry is first added to the timestamp file, are generated
    using platform local time, since we use ``datetime.fromtimestamp``
    to construct them.
    """
    
    datetime_attrs = (
        'year', 'month', 'day',
        'hour', 'minute', 'second',
        'weekday'
    )
    
    def __init__(self, data):
        if isinstance(data, float):
            # It's a file mtime
            self._datetime = datetime.fromtimestamp(data)
        elif isinstance(data, basestring):
            # It's a string timestamp from the cache
            self._datetime = datetime(*map(int, data.split('-')))
        else:
            raise ValueError("{!r} is not a valid entry timestamp".format(data))
        for attr in self.datetime_attrs:
            setattr(self, attr, getattr(self._datetime, attr))
    
    def __repr__(self):
        return "Timestamp: {!r}".format(self._datetime)
    
    def __str__(self):
        dt = self._datetime
        return '-'.join(
            '{:02d}'.format(i)
            for i in (dt.year, dt.month, dt.day, dt.hour, dt.minute)
        )
    
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
        return os.path.getmtime(self.filename)


class TimestampsExtension(BlogExtension):
    """Cache entry timestamps.
    """
    
    entry_mixin = TimestampEntryMixin
