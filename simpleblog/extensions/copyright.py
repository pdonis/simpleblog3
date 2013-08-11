#!/usr/bin/env python3
"""
Module COPYRIGHT -- Simple Blog Copyright Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.decotools import cached_method

from simpleblog.extensions import BlogExtension


class CopyrightExtension(BlogExtension):
    """Add copyright information to blog metadata.
    """
    
    config_vars = dict(
        copyright_template="Copyright {yearspec}",
        copyright_display_template="Copyright &copy; {yearspec}",
        copyright_start_year=None,
        copyright_end_year=None
    )
    
    @cached_method
    def entry_years(self, blog):
        return [entry.timestamp.year for entry in blog.all_entries]
    
    @cached_method
    def start_year(self, blog):
        return min(self.entry_years(blog))
    
    @cached_method
    def end_year(self, blog):
        return max(self.entry_years(blog))
    
    def blog_mod_default_metadata(self, blog, data):
        start_year=self.copyright_start_year or self.start_year(blog)
        end_year=self.copyright_end_year or self.end_year(blog)
        params = dict(
            data,
            yearspec="{}-{}".format(start_year, end_year) if start_year < end_year else start_year
        )
        data.update(
            copyright=self.copyright_template.format(**params),
            copyright_display=self.copyright_display_template.format(**params),
        )
        return data
