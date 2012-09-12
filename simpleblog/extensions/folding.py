#!/usr/bin/env python
"""
Module FOLDING -- Simple Blog Folding Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.decotools import cached_property, cached_method
from plib.stdlib.strings import universal_newline

from simpleblog import (
    extendable_property, extendable_method,
    noresult)
from simpleblog.extensions import BlogExtension


class FoldEntryMixin(object):
    
    @cached_property
    def fold_symbol(self):
        return self.config.get('fold_symbol', "<!-- FOLD -->")
    
    @cached_property
    def fold_inline(self):
        return self.config.get('fold_inline', False)
    
    @extendable_property()
    def fold_marker(self):
        if self.fold_inline:
            return self.fold_symbol
        return '{0}{1}'.format(self.fold_symbol, universal_newline)
    
    def _do_load(self):
        raw = super(FoldEntryMixin, self)._do_load()
        if self.fold_marker in raw:
            short, src = raw.split(self.fold_marker, 1)
            self._short = short
            raw = ''.join((short, src))
        else:
            self._short = None
        return raw
    
    @cached_property
    def short_formats(self):
        return set(self.config.get('short_formats', ["html"]))
    
    @cached_method
    def has_short(self, format):
        self.load()
        if format in self.short_formats:
            try:
                return self._short is not None
            except AttributeError:
                pass
        return False
    
    @extendable_method()
    def short_template(self, format):
        if format in self.short_formats:
            return self.template_data("short", format)
        raise NotImplementedError
    
    @extendable_property()
    def rendered_short(self):
        self.load()
        return self.render(self._short)


class FoldingExtension(BlogExtension):
    """Generate short version of entry for index pages.
    """
    
    entry_mixin = FoldEntryMixin
    
    def page_mod_entry_params(self, page, params, entry):
        params.update(
            index=page.entries.index(entry)
        )
        return params
    
    @cached_property
    def max_index_full(self):
        return max(self.config.get('max_full_entries', 1) - 1, 0)
    
    def entry_get_body(self, entry, format, params):
        if (params.index > self.max_index_full) and entry.has_short(format):
            return entry.short_template(format).format(
                body=entry.rendered_short,
                link=entry.make_permalink(format)
            )
        # If no short form, don't override
        return noresult
