#!/usr/bin/env python
"""
Module RENDER_MARKDOWN -- Simple Blog Markdown Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from markdown import markdown

from plib.stdlib.decotools import cached_property

from simpleblog import BlogMixin, newline
from simpleblog.extensions import BlogExtension


class MarkdownEntryMixin(BlogMixin):
    
    config_vars = dict(
        output_format=('markdown_format', "html4"),
        pretty_print=('markdown_pretty', False)
    )
    
    def _do_render(self, rawdata):
        html = markdown(rawdata, output_format=self.output_format)
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
                if not line.endswith(u"</blockquote>"):
                    out.append(u"")
                blankline_flag = False
            if in_blockquote:
                if line.endswith(u"</blockquote>"):
                    in_blockquote = False
                else:
                    line = u"  {}".format(line)
            else:
                if line.startswith(u"<blockquote>"):
                    in_blockquote = True
            out.append(line)
            if (
                line.endswith(u"</p>") or
                line.endswith(u"</h1>") or
                line.endswith(u"</pre>") or
                line.endswith(u"</blockquote>")
            ):
                blankline_flag = True
        return newline.join(out)


class MarkdownExtension(BlogExtension):
    """Markdown parsing of entry source.
    """
    
    entry_mixin = MarkdownEntryMixin
