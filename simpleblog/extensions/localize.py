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
    """Allow metadata to specify localization for blog.
    """
    
    def blog_post_init(self, blog):
        try:
            blog.metadata.setdefault('locale', u"{0}_{1}.{2}".format(
                blog.metadata['language'],
                blog.metadata['country'],
                blog.metadata['charset']
            ))
        except AttributeError:
            pass
