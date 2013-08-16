#!/usr/bin/env python3
"""
Module TITLE -- Simple Blog Title Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import re

from plib.stdlib.decotools import cached_property

from simpleblog import shared_property, extendable_property, newline
from simpleblog.caching import cached
from simpleblog.extensions import BlogExtension, EntryMixin


titles_file = BlogExtension.config.get('titles_file', "titles")


class TitleEntryMixin(EntryMixin):
    
    config_vars = dict(
        title_separator=newline,
        title_format=False
    )
    
    def _do_load(self):
        raw = super(TitleEntryMixin, self)._do_load()
        if self.title_separator in raw:
            self._titlestr, raw = raw.split(self.title_separator, 1)
        else:
            self._titlestr = ""
        return raw
    
    @shared_property
    def title_rexps(self):
        return [(re.compile(r), s) for r, s in [
            (r"\*\*([A-Za-z0-9]+)\*\*", "<strong>\g<1></strong>"),
            (r"\*([A-Za-z0-9]+)\*", "<em>\g<1></em>")
        ]]
    
    def _format_title(self):
        if self._titlestr and self.title_format:
            for rexp, repl in self.title_rexps:
                self._titlestr = rexp.sub(repl, self._titlestr)
        return self._titlestr
    
    @extendable_property(
        cached(titles_file)
    )
    def title(self):
        self.load()
        return self._format_title()


class TitleExtension(BlogExtension):
    """Parse entry title out of entry source.
    """
    pass
