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


def changed(data, path):
    """Check if ``data`` is changed from the file data at ``path``.
    """
    
    if (not os.path.isfile(path)) or (os.stat(path).st_size != len(data)):
        return True
    with open(path, 'r') as f:
        olddata = f.read()
    return data != olddata


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
        })
    )
    
    def run(self, blog):
        for page in blog.pages:
            data = page.formatted
            path = os.path.abspath(os.path.join(self.static_dir, page.filepath))
            if self.opts.force or changed(data, path):
                if not self.opts.quiet:
                    print "Rendering", path
                dir = os.path.split(path)[0]
                if not os.path.isdir(dir):
                    os.makedirs(dir)
                with open(path, 'w') as f:
                    f.write(data)
            else:
                if not self.opts.quiet:
                    print path, "is unchanged"
