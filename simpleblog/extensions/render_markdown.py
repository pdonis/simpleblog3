#!/usr/bin/env python
"""
Module RENDER_MARKDOWN -- Simple Blog Markdown Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from markdown import markdown

from simpleblog import html_newline
from simpleblog.extensions import BlogExtension


class MarkdownEntryMixin(object):
    
    def _do_render(self, rawdata):
        html = markdown(rawdata, output_format="html4")
        
        # Extra pretty formatting to match the behavior
        # of the Pyblosxom markdown formatter (indent
        # blockquotes and add blank lines between
        # paragraphs)
        lines = html.split(html_newline)
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
        return html_newline.join(out)


class MarkdownExtension(BlogExtension):
    """Markdown parsing of entry source.
    """
    
    entry_mixin = MarkdownEntryMixin
