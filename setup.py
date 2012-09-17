#!/usr/bin/env python -u
"""
Setup script for SIMPLEBLOG package
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import os
from datetime import datetime
from itertools import islice, takewhile


name = "simpleblog"

version = "0.2"

description = "A simple Python blogging system."

author = "Peter A. Donis"

author_email = "peterdonis@alum.mit.edu"

mdnames = ("CHANGES", "README")


h3_prefix = '### '


def h3_underline(line, underline='~'):
    if line.endswith('\n'):
        line = line[:-1]
    return "{}\n".format(underline * len(line))


def rst_from_md(basename):
    with open("{}.md".format(basename), 'rU') as f:
        lines = f.readlines()
    outlines = [
        "**{}** for SIMPLEBLOG {}\n".format(basename, version),
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
    with open(basename, 'w') as f:
        f.writelines(outlines)


for basename in mdnames:
    rst_from_md(basename)


def long_description(filename="README", startline=5, endspec="Copyright and License"):
    with open(filename, 'rU') as f:
        lines = f.readlines()
    return "".join(takewhile(
        lambda line: not line.startswith(endspec),
        islice(lines, startline, None)
    ))


def pypi_url(name):
    return "http://pypi.python.org/pypi/{}".format(name)


classifiers="""
Development Status :: 3 - Alpha
Environment :: Console
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License v2 (GPLv2)
Operating System :: POSIX
Operating System :: POSIX :: Linux
Programming Language :: Python
"""


requires = """
plib (>=0.8.1)
"""

listnames = ('classifiers', 'requires')


for listname in listnames:
    globals()[listname] = globals()[listname].strip().splitlines()


def dir_to_package(dirname):
    return dirname.replace(os.sep, '.')


def package_paths(name):
    return [
        dirname
        for dirname, _, filenames in os.walk(name)
        if "__init__.py" in filenames
    ]


def autodiscover_packages(name):
    return [
        dir_to_package(dirname)
        for dirname in package_paths(name)
    ]


def package_data_paths(pathname):
    return [
        "{}/*".format(dirname[len(pathname) + len(os.sep):])
        for dirname, _, filenames in os.walk(pathname)
        if "__init__.py" not in filenames
    ]


def autodiscover_package_data(name):
    return dict(
        (dir_to_package(pathname), package_data_paths(pathname))
        for pathname in package_paths(name)
        if package_data_paths(pathname)
    )


def autodiscover_scripts(dirname="scripts"):
    return [
        os.path.join(dirname, filename)
        for filename in os.listdir(dirname)
    ]


if __name__ == '__main__':
    from distutils.core import setup
    setup(
        name=name,
        version=version,
        description=description,
        long_description=long_description(),
        author=author,
        author_email=author_email,
        url=pypi_url(name),
        classifiers=classifiers,
        requires=requires,
        packages=autodiscover_packages(name),
        package_data=autodiscover_package_data(name),
        scripts=autodiscover_scripts()
    )
