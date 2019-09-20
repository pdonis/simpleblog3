#!/usr/bin/env python3 -u
"""
Setup script for SIMPLEBLOG package
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from simpleblog import __version__ as version

name = "simpleblog3"
description = "A simple Python 3 blogging system."

startline = 5
endspec = "Copyright and License"

author = "Peter A. Donis"
author_email = "peterdonis@alum.mit.edu"

data_dirs = ["examples"]

dev_status = "Beta"

license = "GPLv2"

classifiers="""
Environment :: Console
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
Operating System :: POSIX
Operating System :: POSIX :: Linux
"""

requires = """
plib3.stdlib (>=0.9.2)
"""

rst_header_template = """**{basename}** for {name} {version}

:Author:        {author}
:Release Date:  {releasedate}
"""


if __name__ == '__main__':
    import sys
    import os
    from subprocess import call
    from distutils.core import setup
    from setuputils import convert_md_to_rst, current_date, setup_vars, long_description as make_long_description
    
    if os.path.isfile("README.md"):
        startline = 3
        long_description = make_long_description(globals(), filename="README.md")
    
    if "sdist" in sys.argv:
        convert_md_to_rst(rst_header_template,
            startline=2,
            name=name.upper(),
            version=version,
            author=author,
            releasedate=current_date("%d %b %Y")
        )
        call(['sed', '-i', 's/bitbucket.org\/pdonis\/plib-/pypi.python.org\/pypi\/plib./', 'README'])
        call(['sed', '-i', 's/bitbucket.org\/pdonis\/plib3-/pypi.python.org\/pypi\/plib3./', 'README'])
        call(['sed', '-i', 's/github.com\/pdonis/pypi.python.org\/pypi/', 'README'])
    
    setup(**setup_vars(globals()))
