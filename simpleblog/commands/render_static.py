#!/usr/bin/env python3
"""
Module RENDER_STATIC -- Simple Blog Static Rendering
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from codecs import encode
from importlib import import_module

from plib.stdlib.classtools import first_subclass
from plib.stdlib.ostools import data_changed
from plib.stdlib.systools import tmp_sys_path

from simpleblog.commands import BlogCommand


class RenderStatic(BlogCommand):
    """Static rendering of all blog pages.
    """
    
    config_vars = dict(
        static_dir="static",
        markdown_highlight_style=None
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
        items = [(page.encoded, page.filepath) for page in blog.pages]
        
        if self.markdown_highlight_style:
            from pygments.style import Style
            from pygments.styles import get_style_by_name
            from pygments.formatters import HtmlFormatter
            
            # User-defined custom style takes precedence
            try:
                with tmp_sys_path(self.config.get('command_dir', "")):
                    mod = import_module(self.markdown_highlight_style)
            except ImportError:
                mdstyle = None
            else:
                mdstyle = first_subclass(mod, Style)
            
            # Try for built-in style if no custom style
            if not mdstyle:
                mdstyle = get_style_by_name(self.markdown_highlight_style)
            
            # Generate CSS with selector for markdown codehilite extension
            css = HtmlFormatter(style=mdstyle).get_style_defs(arg=".codehilite")
            if not css.endswith(os.linesep):
                css = "{}{}".format(css, os.linesep)
            csspath = blog.metadata['highlight_stylesheet_url']
            if csspath.startswith('/'):
                csspath = csspath[1:]
            items.append((encode(css, blog.metadata['charset']), csspath))
        
        for data, path in items:
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
