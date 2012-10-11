#!/usr/bin/env python
"""
Module EXT -- Simple Blog Extension Loader
Package SIMPLEBLOG
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from simpleblog import BlogError
from simpleblog.extensions import BlogExtension
from simpleblog.sub import load_subs


class BlogExtensionError(BlogError):
    pass


def load(config, extensions):
    # This hack is useful for extensions that need to access the
    # config in module or class level code, e.g., in decorators
    BlogExtension.config = config
    exts = load_subs(extensions,
        "extension", config.get('extension_dir', ""),
        BlogExtensionError, BlogExtension)
    for mod, klass in exts:
        mod.extension = klass(config)
