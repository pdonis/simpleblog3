#!/usr/bin/env python
"""
Module TIMEZONE -- Simple Blog Time Zone Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from datetime import datetime, timedelta

import pytz

from plib.stdlib.tztools import local_tzname

from simpleblog import extendable_property
from simpleblog.extensions import BlogExtension, EntryMixin


class TimezoneEntryMixin(EntryMixin):
    
    config_vars = dict(
        utc_timestamps=False,
        timezone_name=""
    )
    
    _tzname = ""
    
    @extendable_property()
    def timezone_tzname(self):
        return self._tzname or self.timezone_name or ("UTC" if self.utc_timestamps else local_tzname())
    
    @extendable_property()
    def timezone(self):
        return pytz.timezone(self.timezone_tzname)


class TimezoneExtension(BlogExtension):
    """Assign a specific time zone to your blog for displaying timestamps.
    
    This extension allows you to specify a timezone name for your blog,
    from among the allowed names in the ``pytz`` library, which is required
    if you want to use this extension.
    
    Note that this extension ignores the ``utc_timestamps`` config setting
    if the ``timezone_name`` config setting is present; if it is absent,
    and ``utc_timestamps`` is true, the pytz UTC timezone will be used;
    otherwise, the pytz timezone whose name corresponds with the name of
    the system's local time zone is used, if it can be found (if not, an
    exception is raised).
    """
    
    config_vars = dict(
        warn_on_timezone_mismatch=False,
    )
    
    def entry_get_datetime_from_mtime(self, entry, mtime):
        dt_naive = datetime.utcfromtimestamp(entry.mtime)
        # Can't use datetime constructor with pytz tzinfo object, per pytz docs
        # (UTC is supposed to work OK, but we'll take no chances), so we build
        # a new "naive" UTC datetime and localize it using the pytz API
        dt_utc = pytz.utc.localize(dt_naive)
        return dt_utc.astimezone(entry.timezone)
    
    def entry_get_string_from_datetime(self, entry, dt, fmt):
        assert dt.dst() is not None  # make sure dt is not "naive"
        idst = 0 if dt.dst() == timedelta(0) else 1
        return "{} {} {}".format(dt.strftime(fmt), entry.timezone_tzname, idst)
    
    def entry_get_datetime_from_string(self, entry, s, fmt):
        s, tzname, sdst = s.rsplit(' ', 2)
        if tzname != entry.timezone_tzname:
            # This flags the entry as having a "mismatched" time zone (i.e., a
            # different time zone from the blog's current default); this is why
            # we only do this if there is indeed a mismatch
            if self.warn_on_timezone_mismatch:
                # FIXME: Allow control of debug output/logging
                print("Mismatched time zone in entry!")
            entry._tzname = tzname
        dt_naive = datetime.strptime(s, fmt)
        return entry.timezone.localize(dt_naive, is_dst=bool(sdst))
