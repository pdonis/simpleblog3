#!/usr/bin/env python
"""
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""


class BlogCommand(object):
    """Base class for command mechanism.
    """
    
    options = None
    arguments = None
    description = None
    epilog = None
    
    def __init__(self, opts, args):
        self.opts = opts
        self.args = args
    
    def run(self, config, blog):
        raise NotImplementedError
