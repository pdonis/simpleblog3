#!/usr/bin/env python
"""
Module SERVE_LOCAL -- Simple Blog Test Server
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from contextlib import contextmanager
import SimpleHTTPServer
import BaseHTTPServer

from simpleblog.commands import BlogCommand


@contextmanager
def tmp_chdir(newdir):
    oldcwd = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(oldcwd)


class ServeLocal(BlogCommand):
    """Serve blog on localhost for testing.
    """
    
    config_vars = dict(
        static_dir="static"
    )
    
    options = (
        ("-n", "--hostname", {
            'action': 'store', 'type': str,
            'default': "localhost",
            'help': "host name or IP address"
        }),
        ("-p", "--port", {
            'action': 'store', 'type': int,
            'default': 8000,
            'help': "port number"
        }),
        ("-q", "--quiet", {
            'action': 'store_true',
            'help': "suppress console output"
        }),
    )
    
    def run(self, blog):
        http_root = os.path.abspath(self.static_dir)
        server_class = BaseHTTPServer.HTTPServer
        handler_class = SimpleHTTPServer.SimpleHTTPRequestHandler
        server_address = (self.opts.hostname, self.opts.port)
        if not self.opts.quiet:
            print "Serving files under {} at {}".format(
                http_root,
                "http://{}:{:d}/".format(self.opts.hostname, self.opts.port)
            )
        httpd = server_class(server_address, handler_class)
        with tmp_chdir(http_root):
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                if not self.opts.quiet:
                    print "Shutting down...."
