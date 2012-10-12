#!/usr/bin/env python
"""
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from simpleblog import BlogConfigUser


class BlogCommand(BlogConfigUser):
    """Base class for command mechanism.
    """
    
    options = None
    arguments = None
    
    def __init__(self, config, opts, args):
        BlogConfigUser.__init__(self, config)
        self.opts = opts
        self.args = args
    
    def run(self, blog):
        raise NotImplementedError
