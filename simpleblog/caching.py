#!/usr/bin/env python
"""
Module CACHING -- Simple Blog Caching Mechanism
Package SIMPLEBLOG
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from functools import wraps

from plib.stdlib.decotools import cached_property

from simpleblog import BlogObject


class BlogCache(BlogObject):
    """Cache for data associated with blog entries.
    
    This allows the blog structure and metadata to be assembled
    without having to stat or open and load any entry files.
    """
    
    def __init__(self, blog, cachename, reverse=False, objtype=None):
        BlogObject.__init__(self, blog)
        self.cachename = cachename
        self.reverse = reverse
        self.objtype = objtype
    
    @cached_property
    def cache_dir(self):
        return self.config.get('cache_dir', self.entries_dir)
    
    @cached_property
    def filename(self):
        return os.path.join(self.cache_dir, self.cachename)
    
    @cached_property
    def cache(self):
        with open(self.filename, 'rU') as f:
            lines = f.readlines()
        if self.reverse:
            def r(t):
                return tuple(reversed(t))
        else:
            def r(t):
                return t
        if self.objtype:
            def e(t):
                return t[0], self.objtype(t[1])
        else:
            def e(t):
                return t
        return dict(
            e(r(line.split())) for line in lines
        )
    
    def save(self):
        items = self.cache.iteritems()
        if self.reverse:
            items = ((v, k) for k, v in items)
        lines = sorted("{0!s} {1!s}\n".format(a, b) for a, b in items)
        with open(self.filename, 'w') as f:
            f.writelines(lines)


cache_map = {}


def cached(cachename, reverse=False, objtype=None):
    """Decorator for blog entry properties that should be cached.
    """
    
    def decorator(f):
        @wraps(f)
        def fcache(self, *args, **kwargs):
            try:
                cacheobj = cache_map[cachename]
            except KeyError:
                cacheobj = cache_map[cachename] = BlogCache(
                    self.blog, cachename, reverse, objtype
                )
            cache = cacheobj.cache
            try:
                return cache[self.cachekey]
            except KeyError:
                value = f(self, *args, **kwargs)
                if cacheobj.objtype is not None:
                    value = cacheobj.objtype(value)
                cache[self.cachekey] = value
                cacheobj.save()
                return value
        return fcache
    return decorator