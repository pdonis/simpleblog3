#!/usr/bin/env python
"""
Module LOCALIZE -- Simple Blog Localization Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from simpleblog.extensions import BlogExtension


class LocalizeExtension(BlogExtension):
    """Allow config to specify localization for blog.
    """
    
    def post_init(self):
        config = self.config
        try:
            config.settings.setdefault('locale', "{0}_{1}.{2}".format(
                config.language, config.country, config.charset
            ))
        except AttributeError:
            pass
