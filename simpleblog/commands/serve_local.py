#!/usr/bin/env python
"""
Module SERVE_LOCAL -- Simple Blog Test Server
Sub-Package SIMPLEBLOG.COMMANDS
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
import SimpleHTTPServer
import BaseHTTPServer

from simpleblog.commands import BlogCommand


class ServeLocal(BlogCommand):
    """Serve blog on localhost for testing.
    """
    
    config_vars = dict(
        local_host="localhost",
        local_port=8000,
        static_dir="static"
    )
    
    options = (
        ("-q", "--quiet", {
            'action': 'store_true',
            'help': "suppress console output"
        }),
    )
    
    def run(self, blog):
        # realpath fixes things up if static_dir has a .. in it
        oldcwd = os.getcwd()
        http_root = os.path.realpath(os.path.join(oldcwd, self.static_dir))
        os.chdir(http_root)
        server_class = BaseHTTPServer.HTTPServer
        handler_class = SimpleHTTPServer.SimpleHTTPRequestHandler
        server_address = (self.local_host, self.local_port)
        if not self.opts.quiet:
            print "Serving files under %s at %s" % (http_root, "http://%s:%d/" % (self.local_host, self.local_port))
        httpd = server_class(server_address, handler_class)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            if not self.opts.quiet:
                print "Shutting down...."
        finally:
            os.chdir(oldcwd)
