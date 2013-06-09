#!/usr/bin/env python3
"""
Module PUBLISH -- Simple Blog Publisher
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os

from plib.stdlib.proc import process_call

from simpleblog.commands import BlogCommand


class Publish(BlogCommand):
    """Publish blog.
    """
    
    config_vars = dict(
        static_dir="static",
        publish_cmd_name="rsync",
        publish_cmd_options="-rt",
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
            self.publish_cmd_name,
            self.publish_cmd_options,
            os.path.join(os.path.abspath(self.static_dir), "*"),
            "{}@{}:{}".format(self.ssh_user, self.ssh_host, self.ssh_path)
        ])
        if self.opts.debug:
            print(cmdline)
        returncode, output = process_call(cmdline, shell=True)
        if (returncode != 0) or not self.opts.quiet:
            print(output.decode())
        if returncode != 0:
            print("Publish failed with return code {}".format(returncode))
