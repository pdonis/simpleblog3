#!/usr/bin/env python3
"""
Module RENDER_MARKDOWN -- Simple Blog Markdown Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
import re
from codecs import encode
from importlib import import_module

from markdown import Markdown

from plib.stdlib.classtools import first_subclass
from plib.stdlib.systools import tmp_sys_path

from simpleblog import extendable_property, newline
from simpleblog.extensions import BlogExtension, EntryMixin


class BaseFormatter(object):
    """Do-nothing formatter to serve as default.
    """
    
    def format(self, html):
        return html


class PrettyPrinter(BaseFormatter):
    """Pretty-prints HTML to match the Pyblosxom markdown formatter.
    
    Key formatting items are indentation of blockquotes and adding blank
    lines between paragraphs.
    """
    
    def format(self, html):
        lines = html.split(newline)
        out = []
        in_blockquote = False
        blankline_flag = False
        for line in lines:
            if blankline_flag:
                if not line.endswith("</blockquote>"):
                    out.append("")
                blankline_flag = False
            if in_blockquote:
                if line.endswith("</blockquote>"):
                    in_blockquote = False
                else:
                    line = "  {}".format(line)
            else:
                if line.startswith("<blockquote>"):
                    in_blockquote = True
            out.append(line)
            if (
                line.endswith("</p>") or
                line.endswith("</h1>") or
                line.endswith("</pre>") or
                line.endswith("</blockquote>")
            ):
                blankline_flag = True
        return newline.join(out)


class MarkdownEntryMixin(EntryMixin):
    
    config_vars = dict(
        output_format=('markdown_format', "html4"),
        highlight_code=('markdown_highlight', False),
        highlight_auto=('markdown_highlight_auto', False),
        pretty_print=('markdown_pretty', False)
    )
    
    @extendable_property()
    def converter(self):
        kwargs = dict(
            output_format=self.output_format
        )
        if self.highlight_code:
            kwargs.update(
                extensions=['codehilite(guess_lang={})'.format(self.highlight_auto)]
            )
        return Markdown(**kwargs)
    
    @extendable_property()
    def formatter(self):
        return PrettyPrinter() if self.pretty_print else BaseFormatter()
    
    def _do_render(self, rawdata):
        html = self.converter.convert(rawdata)
        return self.formatter.format(html)


class MarkdownExtension(BlogExtension):
    """Markdown parsing of entry source.
    """
    
    config_vars = dict(
        markdown_highlight_style=None
    )
    
    def blog_mod_render_items(self, blog, items):
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
        
        return items
