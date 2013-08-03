#!/usr/bin/env python3
"""
Module RENDER_MARKDOWN -- Simple Blog Markdown Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import re

from markdown import Markdown

from simpleblog import newline
from simpleblog.extensions import BlogExtension, EntryMixin


class MarkdownEntryMixin(EntryMixin):
    
    config_vars = dict(
        output_format=('markdown_format', "html4"),
        highlight_code=('markdown_highlight', False),
        highlight_auto=('markdown_highlight_auto', False),
        pretty_print=('markdown_pretty', False)
    )
    
    def _do_render(self, rawdata):
        kwargs = dict(
            output_format=self.output_format
        )
        if self.highlight_code:
            kwargs.update(
                extensions=['codehilite(guess_lang={})'.format(self.highlight_auto)]
            )
        md = Markdown(**kwargs)
        html = md.convert(rawdata)
        if not self.pretty_print:
            return html
        
        # Extra pretty formatting to match the behavior
        # of the Pyblosxom markdown formatter (indent
        # blockquotes and add blank lines between
        # paragraphs)
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


class MarkdownExtension(BlogExtension):
    """Markdown parsing of entry source.
    """
    pass
