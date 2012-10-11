#!/usr/bin/env python
"""
Module PUBLISH -- Simple Blog Publisher
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from subprocess import check_output, STDOUT, CalledProcessError

from simpleblog.commands import BlogCommand


class Publish(BlogCommand):
    """Publish blog.
    """
    
    config_vars = dict(
        static_dir="static",
        cmd_name="rsync",
        cmd_options="-rt",
        ssh_user="",
        ssh_host="",
        ssh_path="~/",
    )
    
    options = (
        ("-q", "--quiet", {
            'action': 'store_true',
            'help': "suppress console output"
        }),
        ("-d", "--debug", {
            'action': 'store_true',
            'help': "print rsync command line for debugging"
        })
    )
    
    def run(self, blog):
        cmdline = ' '.join([
            self.cmd_name,
            self.cmd_options,
            os.path.join(os.path.abspath(self.static_dir), "*"),
            "{}@{}:{}".format(self.ssh_user, self.ssh_host, self.ssh_path)
        ])
        if self.opts.debug:
            print cmdline
        try:
            output = check_output(cmdline, stderr=STDOUT, shell=True)
        except CalledProcessError, e:
            output = e.output
            returncode = e.returncode
        else:
            returncode = 0
        if (returncode != 0) or not self.opts.quiet:
            print output
        if returncode != 0:
            print "Publish failed with return code {}".format(returncode)
