#!/usr/bin/env python -u
"""
Setup script for SIMPLEBLOG package
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from datetime import datetime
from itertools import islice, takewhile

from distutils.core import setup


version = "0.1"

h3_prefix = '### '


def h3_underline(line, underline='~'):
    if line.endswith('\n'):
        line = line[:-1]
    return "{}\n".format(underline * len(line))


def make_readme(filename="README.md"):
    with open(filename, 'rU') as f:
        lines = f.readlines()
    outlines = [
        "**README** for SIMPLEBLOG {}\n".format(version),
        "\n",
        ":Author:        Peter A. Donis\n",
        ":Release Date:  {}\n".format(datetime.now().strftime("%d %b %Y"))
    ]
    for line in islice(lines, 2, None):
        is_h3line = line.startswith(h3_prefix)
        if is_h3line:
            line = line[len(h3_prefix):]
        outlines.append(line)
        if is_h3line:
            outlines.append(h3_underline(line))
    with open("README", 'w') as f:
        f.writelines(outlines)


def long_description(filename="README"):
    with open(filename, 'rU') as f:
        lines = f.readlines()
    return "".join(takewhile(
        lambda line: not line.startswith("Copyright and License"),
        islice(lines, 5, None)
    ))


make_readme()

setup(
    name="simpleblog",
    version=version,
    description="A simple Python blogging system.",
    long_description=long_description(),
    author="Peter A. Donis",
    author_email="peterdonis@alum.mit.edu",
    url="http://pypi.python.org/pypi/simpleblog",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python"
    ],
    requires=[
        'plib (>=0.8)',
        'yaml'
    ],
    packages=[
        'simpleblog',
        'simpleblog.commands',
        'simpleblog.extensions'
    ],
    scripts=[
        'scripts/simpleblog-run'
    ]
)
