#!/usr/bin/env python
"""
Module RENDER_STATIC -- Simple Blog Static Rendering
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os

from simpleblog.commands import BlogCommand


class RenderStatic(BlogCommand):
    """Static rendering of all blog pages.
    """
    
    def run(self, config, blog):
        for page in blog.pages:
            data = page.formatted
            path = os.path.abspath("{0}{1}".format(
                config.get('static_dir', "static"), page.urlpath
            ))  # FIXME make this portable
            print "Rendering", path
            dir = os.path.split(path)[0]
            if not os.path.isdir(dir):
                os.makedirs(dir)
            with open(path, 'w') as f:
                f.write(data)
