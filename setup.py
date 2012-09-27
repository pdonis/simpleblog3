#!/usr/bin/env python -u
"""
Setup script for SIMPLEBLOG package
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""


name = "simpleblog"
version = "0.3"
description = "A simple Python blogging system."

startline = 5
endspec = "Copyright and License"

author = "Peter A. Donis"
author_email = "peterdonis@alum.mit.edu"

data_dirs = ["examples"]

dev_status = "Alpha"

license = "GPLv2"

classifiers="""
Environment :: Console
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
Operating System :: POSIX
Operating System :: POSIX :: Linux
"""

requires = """
plib (>=0.8.2)
"""

rst_header_template = """**{basename}** for {name} {version}

:Author:        {author}
:Release Date:  {releasedate}
"""


if __name__ == '__main__':
    from distutils.core import setup
    from setuputils import convert_md_to_rst, current_date, setup_vars
    
    convert_md_to_rst(rst_header_template,
        startline=2,
        name=name.upper(),
        version=version,
        author=author,
        releasedate=current_date("%d %b %Y")
    )
    
    setup(**setup_vars(globals()))
