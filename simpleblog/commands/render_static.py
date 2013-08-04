#!/usr/bin/env python3
"""
Module RENDER_STATIC -- Simple Blog Static Rendering
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os

from plib.stdlib.ostools import data_changed

from simpleblog.commands import BlogCommand


class RenderStatic(BlogCommand):
    """Static rendering of all blog pages.
    """
    
    config_vars = dict(
        static_dir="static"
    )
    
    options = (
        ("-f", "--force", {
            'action': 'store_true',
            'help': "force writing of unchanged files"
        }),
        ("-q", "--quiet", {
            'action': 'store_true',
            'help': "suppress console output"
        }),
        ("-u", "--show-unchanged", {
            'action': 'store_true',
            'help': "show console output for unchanged files"
        })
    )
    
    def run(self, blog):
        for data, path in blog.render_items:
            path = os.path.abspath(os.path.join(self.static_dir, path))
            if self.opts.force or data_changed(data, path):
                if not self.opts.quiet:
                    print("Rendering", path)
                dir = os.path.split(path)[0]
                if not os.path.isdir(dir):
                    os.makedirs(dir)
                with open(path, 'wb') as f:
                    f.write(data)
            else:
                if self.opts.show_unchanged:
                    print(path, "is unchanged")
