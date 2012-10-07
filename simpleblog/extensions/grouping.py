#!/usr/bin/env python
"""
Module GROUPING -- Simple Blog Grouping Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from itertools import groupby
from operator import attrgetter

from plib.stdlib.decotools import cached_property

from simpleblog import BlogMixin, extendable_property, BlogEntry
from simpleblog.extensions import BlogExtension


class GroupingPageMixin(BlogMixin):
    
    config_vars = dict(
        groupindex_key='groupindex',
        group_key='datestamp_formatted',
        group_formats=dict(
            vartype=set,
            default=["html"])
    )
    
    @extendable_property()
    def group_head_template(self):
        return self.template_data("group", "head")
    
    @extendable_property()
    def group_foot_template(self):
        return self.template_data("group", "foot")
    
    def _get_format_entries(self):
        if self.format in self.group_formats:
            for groupindex, (groupkey, group) in enumerate(groupby(
                self.entries, attrgetter(self.group_key)
            )):
                params = {
                    self.groupindex_key: groupindex,
                    self.group_key: groupkey
                }
                yield self.group_head_template.format(**params)
                group_params = dict(
                    groupindex=groupindex,
                    groupkey=groupkey
                )
                for entry in group:
                    entryparams = self.entry_params(entry)
                    entryparams.update(group_params)
                    yield entry.formatted(self.format, entryparams)
                yield self.group_foot_template.format(**params)
        else:
            for item in super(GroupingPageMixin, self)._get_format_entries():
                yield item


class GroupingExtension(BlogExtension):
    """Group page entries by date.
    """
    
    page_mixin = GroupingPageMixin
