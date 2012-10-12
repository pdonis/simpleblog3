#!/usr/bin/env python
"""
Module RUN -- Simple Blog Command Runner
Package SIMPLEBLOG
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from plib.stdlib.options import prepare_specs, update_parser, invoke_parser

from simpleblog import BlogError, load_blog
from simpleblog.commands import BlogCommand
from simpleblog.sub import load_sub


class BlogCommandError(BlogError):
    pass


def run(cmdname, parser, opts, goptlist, result=None, remaining=None):
    config, blog = load_blog(opts)
    
    mod, klass = load_sub(cmdname,
        "command", config.get('command_dir', ""),
        BlogCommandError, BlogCommand)
    
    optlist, arglist = prepare_specs(klass.options or (), klass.arguments or ())
    update_parser(parser, optlist, arglist)
    opts, args = invoke_parser(parser, goptlist + optlist, arglist, remaining, result)
    
    if opts.help:
        # Hack to make it look like the help is specific to cmdname; this is
        # *not* documented in the argparse module ;) (actually, we rely in
        # part on plib.stdlib.options setting the metavar keyword)
        for action in parser._actions:
            if action.metavar == "COMMAND":
                action.metavar = cmdname  # this displays the specific command name
                action.nargs = 1  # this removes the brackets from the command name
                # There can be only one
                break
        parser.print_help()
    else:
        cmd = klass(config, opts, args)
        cmd.run(blog)
