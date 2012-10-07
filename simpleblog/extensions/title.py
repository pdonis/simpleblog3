#!/usr/bin/env python
"""
Module TITLE -- Simple Blog Title Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.strings import universal_newline

from simpleblog import BlogMixin, extendable_property
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension


titles_file = BlogExtension.config.get('titles_file', "titles")


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
    
    @extendable_property(
        cached(titles_file)
    )
    def title(self):
        self.load()
        return self._titlestr


class TitleExtension(BlogExtension):
    """Parse entry title out of entry source.
    """
    
    entry_mixin = TitleEntryMixin
