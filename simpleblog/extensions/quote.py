#!/usr/bin/env python
"""
Module QUOTE -- Simple Blog Quote Extension
Sub-Package SIMPLEBLOG.EXTENSIONS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from urllib import quote_plus
from urlparse import urljoin

from plib.stdlib.iters import suffixed_items

from simpleblog.extensions import BlogExtension


class QuoteExtension(BlogExtension):
    """Add quoted versions of all URLs to blog metadata.
    """
    
    def blog_mod_required_metadata(self, blog, data):
        data.add(
            'root_url'
        )
        return data
    
    def blog_post_init(self, blog):
        urlkeys = set(suffixed_items(blog.metadata, '_url', full=True))
        tmpl = '{}_quoted'
        for key in urlkeys:
            newkey = tmpl.format(key)
            if newkey not in blog.metadata:
                url = blog.metadata[key]
                if key == 'root_url':
                    url = urljoin(url, "/index.html")
                else:
                    url = urljoin(blog.metadata['root_url'], blog.metadata[key])
                blog.metadata[newkey] = quote_plus(url)
