#!/usr/bin/env python
"""
Module RUN -- Simple Blog Command Runner
Package SIMPLEBLOG
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.options import parse_options

from simpleblog import BlogError, load_sub, load_blog
from simpleblog.commands import BlogCommand


class BlogCommandError(BlogError):
    pass


def run(cmdname, opts, result=None, remaining=None):
    mod, klass = load_sub("command", cmdname,
        BlogCommandError, BlogCommand)
    
    optlist = klass.options or ()
    arglist = klass.arguments or ()
    description = klass.description
    epilog = klass.epilog
    if optlist or arglist or remaining:
        copts, cargs = parse_options(
            optlist, arglist, description, epilog, remaining, result
        )
    
    cmd = klass(copts, cargs)
    config, blog = load_blog(opts)
    cmd.run(config, blog)
