#!/usr/bin/env python
"""
Module TITLE -- Simple Blog Title Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.decotools import cached_property
from plib.stdlib.strings import universal_newline

from simpleblog import BlogMixin
from simpleblog.extensions import BlogExtension


class TitleEntryMixin(BlogMixin):
    
    config_vars = dict(
        title_separator=universal_newline
    )
    
    def _do_load(self):
        raw = super(TitleEntryMixin, self)._do_load()
        if self.title_separator in raw:
            self._titlestr, raw = raw.split(self.title_separator, 1)
        else:
            self._titlestr = ""
        return raw


class TitleExtension(BlogExtension):
    """Parse entry title out of entry source.
    """
    
    entry_mixin = TitleEntryMixin
    
    def entry_get_title(self, entry):
        entry.load()
        return entry._titlestr
