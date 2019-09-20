#!/usr/bin/env python3
"""
Module SETUPUTILS -- Utilities to automate boilerplate in Python setup scripts
Copyright (C) 2012-2013 by Peter A. Donis

Released under the Python Software Foundation License.

The purpose of this module is to help automate away much of the
boilerplate that goes into Python setup scripts. Typical usage:

    # declare variables here, for example...
    
    name = "myprog"
    
    description = "My Python Program"
    
    # other variables depending on what you need, but the autodiscovery
    # capabilities of setuputils remove the need for a lot of manual
    # declarations, or at least make them easier
    
    if __name__ == '__main__':
        from distutils.core import setup
        from setuputils import setup_vars
        setup(**setup_vars(globals()))

Or, you can take more fine-grained control over things by only
invoking particular sub-functions, for example:

    if __name__ == '__main__':
        from distutils.core import setup
        from setuputils import autodiscover_packages
        setup(
            name="myprog",
            description="My Python Program",
            packages=autodiscover_packages(globals()),
            # other args
        )

You can even mix the two methods, disabling general autodiscovery
but using it for particular things:
    
    from setuputils import autodiscover_packages, setup_vars
    
    name = "myprog"
    
    description = "My Python Program"
    
    packages = autodiscover_packages(globals())
    
    if __name__ == '__main__':
        from distutils.core import setup
        setup(**setup_vars(globals(), autodiscover=False))

See the docstrings of the individual functions below for more
information.
"""

import os
from datetime import datetime
from distutils.core import Extension
from functools import partial
from itertools import chain, dropwhile, islice, takewhile


def _rst_header_lines(template, basename, **kwds):
    # Generate header lines from template
    if template:
        return [
            "{}{}".format(line, os.linesep) for line in
            template.format(basename=basename, **kwds).splitlines()
        ]
    return []


def _rst(basename, template, startline=None, rstext="rst", **kwds):
    # Add header to file basename.rst and save to file basename
    with open("{}.{}".format(basename, rstext), 'rU') as f:
        lines = f.readlines()
    outlines = _rst_header_lines(template, basename, **kwds) + lines[startline:]
    with open(basename, 'w') as f:
        f.writelines(outlines)


def convert_rst(template=None,
                dirname=".", rstnames=None, rstext="rst",
                **kwds):
    if rstnames is None:
        rstnames = [
            os.path.splitext(basename)[0]
            for basename in os.listdir(dirname)
            if os.path.splitext(basename)[1] == ".{}".format(rstext)
        ]
    for basename in rstnames:
        _rst(basename, template=template, rstext=rstext, **kwds)


def underline(line, underline='~'):
    """Return an underline string for ``line``.
    
    Intended for use with level 3 and lower headings.
    
    Note that the default for ``underline`` assumes that the level
    1 and 2 underlines are the standard ``=`` and ``-``. You can
    pass a different underline character to this function if needed.
    """
    
    if line.endswith('\n'):
        line = line[:-1]
    return "{}\n".format(underline * len(line))


h3_prefix = '### '


def _rst_from_md(basename, template=None, startline=None, mdext="md", **kwds):
    # Convert Markdown text from file named basename.md to RST
    # text saved to file named basename
    with open("{}.{}".format(basename, mdext), 'rU') as f:
        lines = f.readlines()
    outlines = []
    # Allow adding a header to the RST version (which can
    # be filtered out when generating PKG_INFO if desired)
    outlines.extend(_rst_header_lines(template, basename, **kwds))
    # Normally you will want to pass an integer in as the
    # startline keyword argument, since the Markdown file
    # will probably have a title at the start, and the RST
    # files used to provide PKG_INFO to PyPI should not have
    # title lines (since PyPI adds a title itself)
    for line in islice(lines, startline, None):
        is_h3line = line.startswith(h3_prefix)
        if is_h3line:
            line = line[len(h3_prefix):]
        outlines.append(line)
        if is_h3line:
            outlines.append(underline(line))
    with open(basename, 'w') as f:
        f.writelines(outlines)


def convert_md_to_rst(template=None,
                      dirname=".", mdnames=None, mdext="md",
                      **kwds):
    """Convert Markdown text files to RST text files.
    
    Useful for projects where "official" releases are on PyPI but
    development source is visible somewhere else that uses Markdown
    instead of ReStructuredText as its default text doc format,
    such as github. The ``mdnames`` parameter gives the base names
    of files to be converted; this defaults to every text file in
    directory ``dirname`` (which defaults to the directory your
    setup script is run from) with an ``.md`` extension.
    """
    
    if mdnames is None:
        mdnames = [
            os.path.splitext(basename)[0]
            for basename in os.listdir(dirname)
            if os.path.splitext(basename)[1] == ".{}".format(mdext)
        ]
    for basename in mdnames:
        _rst_from_md(basename, template=template, mdext=mdext, **kwds)


def current_date(fmt):
    return datetime.now().strftime(fmt)


def long_description(varmap, filename="README",
                     startline=None, startspec=None,
                     endline=None, endspec=None):
    """Extract long description suitable for PyPI from RST text file.
    
    Useful to automate generating the ``long_description``
    setup parameter. Looks in ``filename``, which should be
    a ReStructuredText file, and returns all the text from
    the given starting line (which is included in the result)
    to the given ending line (which is not included in the
    result). Lines can be specified either by line number
    (``startline`` or ``endline``) or a string the line
    starts with (``startspec`` or ``endspec``). Defaults
    to using the ``README`` file.
    """
    
    startline = startline or varmap.get('startline')
    startspec = startspec or varmap.get('startspec')
    endline = endline or varmap.get('endline')
    endspec = endspec or varmap.get('endspec')
    
    with open(filename, 'rU') as f:
        lines = f.readlines()
    
    if startline or endline:
        innerlines = islice(lines, startline, endline)
    else:
        innerlines = lines
    if startspec:
        inner = dropwhile(
            lambda line: not line.startswith(startspec),
            innerlines
        )
    else:
        inner = innerlines
    if endspec:
        desclines = takewhile(
            lambda line: not line.startswith(endspec),
            inner
        )
    else:
        desclines = inner
    
    return "".join(desclines)


def pypi_url(varmap):
    """Return the PyPI URL for program ``name`` from the setup vars.
    """
    return "http://pypi.org/project/{}".format(varmap['name'])


def provides(varmap):
    """Return a minimal ``provides`` list from the setup vars.
    """
    
    try:
        return ["{} ({})".format(varmap['name'], varmap['version'])]
    except KeyError:
        return [varmap['name']]


def add_vars(varmap):
    """Automate adding ``long_description`` and ``url`` setup vars.
    """
    
    if 'long_description' not in varmap:
        varmap['long_description'] = long_description(varmap)
    if 'url' not in varmap:
        varmap['url'] = pypi_url(varmap)
    # provides format changed and it's not used anyway, so don't automatically include it


def convert_lists(varmap,
                  listnames=('classifiers', 'requires', 'provides', 'obsoletes')):
    """Convert long strings to lists of strings.
    
    Allows variable names in ``listnames`` to be specified as
    long strings instead of lists, for easier typing. The
    ``license_map`` and ``devstatus_trove`` strings below give
    examples of the kind of long strings that can be used.
    """
    
    listnames = varmap.get('listnames', listnames)
    for listname in listnames:
        try:
            var = varmap[listname]
        except KeyError:
            pass
        else:
            if isinstance(var, str):
                varmap[listname] = var.strip().splitlines()


def add_classifier_python(varmap):
    """Automate adding the Python language classifier.
    
    Since most programs using this module will be Python
    programs, this makes it easy to ensure that the Python
    language Trove classifier is present.
    """
    
    classifiers = varmap.setdefault('classifiers', [])
    if all(not c.startswith("Programming Language ::") for c in classifiers):
        classifiers.append("Programming Language :: Python :: 3")


license_map = dict(zip("""
AFL
Apache
BSD
AGPLv3
AGPLv3+
FDL
GPL
GPLv2
GPLv2+
GPLv3
GPLv3+
LGPLv2
LGPLv2+
LGPLv3
LGPLv3+
LGPL
MIT
MPL
MPL 1.1
MPL 2.0
CNRI
PSF
QPL
""".strip().splitlines(),"""
License :: OSI Approved :: Academic Free License (AFL)
License :: OSI Approved :: Apache Software License
License :: OSI Approved :: BSD License
License :: OSI Approved :: GNU Affero General Public License v3
License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)
License :: OSI Approved :: GNU Free Documentation License (FDL)
License :: OSI Approved :: GNU General Public License (GPL)
License :: OSI Approved :: GNU General Public License v2 (GPLv2)
License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
License :: OSI Approved :: GNU General Public License v3 (GPLv3)
License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)
License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)
License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)
License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)
License :: OSI Approved :: MIT License
License :: OSI Approved :: Mozilla Public License 1.0 (MPL)
License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)
License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)
License :: OSI Approved :: Python License (CNRI Python License)
License :: OSI Approved :: Python Software Foundation License
License :: OSI Approved :: Qt Public License (QPL)
""".strip().splitlines()))


def add_classifier_license(varmap):
    """Convert ``license`` setup var to Trove classifier.
    
    Allows short specification of common licenses while still
    adhering to the PyPI spec, which says that the ``license``
    setup keyword should only be used for licenses that don't
    have a Trove classifier.
    """
    
    try:
        c = license_map[varmap['license']]
    except KeyError:
        pass
    else:
        varmap.setdefault('classifiers', []).append(c)
        # PyPI docs say the "License" keyword should only be used for
        # licenses that don't have a Trove classifier
        del varmap['license']


devstatus_trove = """
Development Status :: 3 - Alpha
Development Status :: 4 - Beta
Development Status :: 5 - Production/Stable
Development Status :: 6 - Mature
Development Status :: 7 - Inactive
Development Status :: 1 - Planning
Development Status :: 2 - Pre-Alpha
""".strip().splitlines()


def add_classifier_dev_status(varmap):
    """Convert ``dev_status`` setup var to Trove classifier.
    
    Allows short specification of development status instead
    of having to type the full Trove classifier.
    """
    
    try:
        dev_status = varmap['dev_status']
    except KeyError:
        pass
    else:
        for c in devstatus_trove:
            if c.endswith(dev_status):
                varmap.setdefault('classifiers', []).append(c)
                break


def add_classifiers(varmap):
    """Automate adding standard classifiers to setup vars.
    
    Also sorts the list of classifiers for neatness.
    """
    
    add_classifier_python(varmap)
    add_classifier_license(varmap)
    add_classifier_dev_status(varmap)
    varmap['classifiers'] = sorted(varmap['classifiers'])


def package_root(varmap):
    """Return correct directory for the root package.
    
    The "root" package is the one where modules which do not
    belong to a package are located (see the distutils docs).
    This function should not need to be called directly in
    your actual setup script, but it can be useful for testing.
    Note that it looks for a ``package_root`` setup var, which
    can be used as a shortcut if your "root" package is not in
    the standard place (which is your setup script directory),
    rather than having to declare a ``package_dir`` dictionary
    with a ``''`` key.
    """
    
    try:
        return varmap['package_dir']['']
    except KeyError:
        try:
            result = varmap['package_root']
        except KeyError:
            return "."
        else:
            dirmap = varmap.setdefault('package_dir', {})
            if '' not in dirmap:
                dirmap[''] = result
            return result


def autodiscover_modules(varmap, excludes=("setup", "setuputils")):
    """Return list of Python modules in your distro.
    
    Module names listed in ``excludes`` will not be included; by
    default only ``setup.py`` and ``setuputils.py`` are excluded,
    all other ``.py`` files in your "root" package are included.
    """
    
    excludes = varmap.get('mod_excludes', excludes)
    return [
        os.path.splitext(filename)[0]
        for filename in os.listdir(package_root(varmap))
        if (os.path.splitext(filename)[1] == ".py")
        and (os.path.splitext(filename)[0] not in excludes)
    ]


def add_py_modules(varmap):
    """Automatically fill in the ``py_modules`` setup var.
    """
    
    if 'py_modules' not in varmap:
        varmap['py_modules'] = autodiscover_modules(varmap)


def dir_to_package(dirname):
    return dirname.replace(os.sep, '.')


def package_paths(varmap):
    """Return list of directories in your distro that are Python packages.
    
    This function should not need to be called directly in
    your actual setup script, but it can be useful for testing.
    It uses the "root" package, as determined from your setup
    vars, to determine where to start the search.
    """
    
    rootdir = package_root(varmap)
    result = []
    for dirname, subdirs, filenames in os.walk(rootdir):
        if dirname != rootdir:
            if "__init__.py" in filenames:
                result.append(dirname.split(os.sep, 1)[1])
            else:
                # Don't recurse into subdirs in non-packages
                subdirs[:] = []
    return result


def autodiscover_packages(varmap):
    """Return list of Python packages in your distro.
    """
    
    return [
        dir_to_package(dirname)
        for dirname in package_paths(varmap)
    ]


def add_packages(varmap):
    """Automatically fill in the ``packages`` setup var.
    """
    
    if 'packages' not in varmap:
        varmap['packages'] = autodiscover_packages(varmap)


def _package_data_paths(pathname, ext_srcdir):
    # Return list of package subdirectories that are not packages
    # themselves (and are therefore presumed to contain package data)
    return [
        "{}/*.*".format(subdir)
        for subdir in os.listdir(pathname)
        if (subdir != "__pycache__")
        and (subdir != ext_srcdir)
        and os.path.isdir(os.path.join(pathname, subdir))
        and ("__init__.py" not in os.listdir(os.path.join(pathname, subdir)))
    ]


def autodiscover_package_data(varmap, ext_srcdir=""):
    """Return mapping of package data paths to file lists.
    
    The ``ext_srcdir`` argument is used to exclude package
    subdirectories (if any) that contain extension source files.
    Leaving it blank (the default) means all subdirectories of
    all packages are checked.
    """
    
    ext_srcdir = varmap.get('ext_srcdir', ext_srcdir)
    return dict(
        (dir_to_package(pathname), _package_data_paths(pathname, ext_srcdir))
        for pathname in package_paths(varmap)
        if _package_data_paths(pathname, ext_srcdir)
    )


def add_package_data(varmap):
    """Automatically fill in the ``package_data`` setup var.
    """
    
    if 'package_data' not in varmap:
        varmap['package_data'] = autodiscover_package_data(varmap)


def autodiscover_extensions(varmap,
                            ext_srcdir="",
                            ext_exts=(".c", ".cc", ".cpp", ".i")):
    """Return list of ``Extension`` instances for your distro.
    
    Looks at the ``ext_names`` setup var for the names of
    extension modules (dotted names indicate extensions that
    live inside packages). Each extension name is converted
    to a path relative to your "root" package in which the
    extension is located.
    
    The ``ext_srcdir`` argument, if non-blank, indicates that
    extension source files are in a subdirectory of the extension
    directory (for example, the ``src`` subdirectory).
    
    The ``ext_exts`` argument gives the file extensions for source
    files (the default should work for most cases).
    
    Note that this function assumes that only one extension
    "lives" in a given directory; multiple extensions in the
    same directory can't be autodiscovered using this mechanism.
    """
    
    rootdir = package_root(varmap)
    result = []
    try:
        extnames = varmap['ext_names']
    except KeyError:
        pass
    else:
        ext_srcdir = varmap.get('ext_srcdir', ext_srcdir)
        ext_exts = varmap.get('ext_exts', ext_exts)
        for extname in extnames:
            srcpath = os.path.join(
                rootdir,
                os.path.dirname(extname.replace('.', os.sep))
            )
            if ext_srcdir:
                srcpath = os.path.join(srcpath, ext_srcdir)
            sources = [
                "{}/{}".format(srcpath, basename)
                for basename in os.listdir(srcpath)
                if os.path.splitext(basename)[1] in ext_exts
            ]
            result.append(
                Extension(extname, sources)
            )
    return result


def add_extensions(varmap):
    """Automatically fill in the ``ext_modules`` setup var.
    """
    
    if 'ext_modules' not in varmap:
        varmap['ext_modules'] = autodiscover_extensions(varmap)


def autodiscover_datafiles(varmap):
    """Return list of (dist directory, data file list) 2-tuples.
    
    The ``data_dirs`` setup var is used to give a list of
    subdirectories in your source distro that contain data
    files. It is assumed that all such files will go in the
    ``share`` subdirectory of the prefix where distutils is
    installing your distro (see the distutils docs); within
    that directory, a subdirectory with the same name as
    your program (i.e., the ``name`` setup var) will be
    created, and each directory in ``data_dirs`` will be a
    subdirectory of that. So, for example, if you have example
    programs using your distro in the ``"examples"`` directory
    in your distro, you would declare ``data_dirs = "examples"``
    in your setup vars, and everything under that source
    directory would be installed into ``share/myprog/examples``.
    """
    
    result = []
    try:
        datadirs = varmap['data_dirs']
    except KeyError:
        pass
    else:
        pathprefix = "share/{}".format(varmap['name'])
        for datadir in datadirs:
            for dirname, subdirs, filenames in os.walk(datadir):
                if filenames and ("." not in dirname):
                    distdir = dirname.replace(os.sep, '/')
                    distfiles = [
                        "{}/{}".format(distdir, filename)
                        for filename in filenames
                        if not filename.startswith(".")
                    ]
                    if distfiles:
                        distdir = dirname.replace(os.sep, '/')
                        result.append(
                            ("{}/{}".format(pathprefix, distdir), distfiles)
                        )
    return result


def add_datafiles(varmap):
    """Automatically fill in the ``data_files`` setup var.
    """
    
    if 'data_files' not in varmap:
        varmap['data_files'] = autodiscover_datafiles(varmap)


def autodiscover_scripts(varmap, dirname="scripts"):
    """Return a list of scripts in your distro.
    
    The ``dirname`` argument gives the directory in your source
    distro in which to look for scripts. The ``script_dir``
    setup var can be used to customize this if for some strange
    reason you can't use the default of ``"scripts"``.
    """
    
    dirname = varmap.get('script_dir', dirname)
    if os.path.isdir(dirname):
        return [
            os.path.join(dirname, filename)
            for filename in os.listdir(dirname)
        ]
    return []


def add_scripts(varmap):
    """Automatically fill in the ``scripts`` setup var.
    """
    
    if 'scripts' not in varmap:
        varmap['scripts'] = autodiscover_scripts(varmap)


def autodiscover_all(varmap):
    """Automatically fill in all auto-discovered setup variables.
    
    Note that even if you don't use all of these variables
    (for example, your distro may have only packages and no
    py_modules, or you may have no package data, extensions,
    etc.), you can still use this function; if it finds no
    instances of a given item, there is no effect.
    """
    
    add_py_modules(varmap)
    add_packages(varmap)
    add_package_data(varmap)
    add_extensions(varmap)
    add_datafiles(varmap)
    add_scripts(varmap)


def _add_package_data_lines(pdata, lines):
    # Distutils won't automatically include package_data
    # if we have a MANIFEST.in, so we need to include it
    # in MANIFEST.in (actually, there is supposedly a
    # fix for that that's in the head of the Python source
    # tree, but it isn't in all recent versions and
    # distutils will take care of any duplicate file
    # inclusions anyway, so it doesn't hurt to make sure
    # with the "belt and suspenders" approach here)
    for pkgname, items in pdata.items():
        pkgname = pkgname.replace('.', '/')
        for item in items:
            if '/' in item:
                dirname, filespec = item.rsplit('/', 1)
                dirname = "{}/{}".format(pkgname, dirname)
            else:
                dirname = pkgname
                filespec = item
            lines.append(
                "recursive-include {} {}\n".format(dirname, filespec)
            )


def _add_data_dirs_lines(datadirs, lines):
    # Shortcut if data_dirs was specified (in which
    # case we don't need to individually include each
    # file in data_files)
    for datadir in datadirs:
        lines.append(
            "recursive-include {} *.*\n".format(datadir)
        )


def _add_data_files_lines(datafiles, lines):
    # Distutils won't automatically include data_files
    # either if there's a MANIFEST.in (see note above)
    for _, filenames in datafiles:
        for datafile in filenames:
            lines.append(
                "include {}\n".format(datafile)
            )


def _add_scripts_lines(scripts, lines):
    # Same "belt and suspenders" strategy as for package
    # data and data files above; distutils seems to be more
    # consistent about including scripts but...
    for script in scripts:
        lines.append(
            "include {}\n".format(script)
        )


def _add_lines(varmap, key, lines):
    # Factored out for easier use in make_manifest_in
    try:
        data = varmap[key]
    except KeyError:
        return False
    else:
        globals()['_add_{}_lines'.format(key)](data, lines)
        return True


def make_manifest_in(varmap):
    """Automatically generate ``MANIFEST.in`` template.
    
    Most of this can be done automatically based on other
    setup vars, but for any items that are not covered by
    that, you can add a ``MANIFEST.in.in`` template that
    declares those items. That template will occur last in
    the generated ``MANIFEST.in`` file, so it can also be
    used, if necessary, to override any of the automatically
    generated items.
    
    Note that ``setuputils.py`` is automatically included,
    since it is assumed it should be treated the same as
    ``setup.py``.
    
    Also note that files implied by the ``package_data``,
    ``data_files`` (or ``data_dirs`` if ``data_files`` is
    not present), and ``scripts`` setup vars are also included
    in the generated ``MANIFEST.in``. The Python distutils
    are not completely consistent in including these files
    if a ``MANIFEST.in`` template is used, so we make sure
    by including them here (the distutils automatically
    ignore duplicate file specs so there is no harm done
    either way).
    """
    
    lines = ["include setuputils.py\n"]
    
    # Add lines for things that distutils doesn't always
    # add automatically (see comments in subfunctions above)
    for key in ('package_data', ('data_dirs', 'data_files'), 'scripts'):
        if isinstance(key, tuple):
            for k in key:
                if _add_lines(varmap, k, lines):
                    break
        else:
            _add_lines(varmap, key, lines)
    
    # This ensures that pyc files are left out in case the source
    # tree has them from testing
    lines.append("recursive-exclude . *.pyc\n")
    
    # Read from the in.in file last so the user can override
    # any of the above (shouldn't need to but just in case)
    try:
        with open("MANIFEST.in.in", 'rU') as f:
            in_in_lines = f.readlines()
    except IOError:
        pass
    else:
        lines.extend(in_in_lines)
    
    with open("MANIFEST.in", 'w') as f:
        f.writelines(lines)


# The type values in this dict are not currently used, but
# may be used in future

distutils_keywords = dict(
    name=str,
    version=str,
    description=str,
    long_description=str,
    author=str,
    author_email=str,
    maintainer=str,
    maintainer_email=str,
    url=str,
    download_url=str,
    packages=list,
    py_modules=list,
    scripts=list,
    ext_modules=list,
    classifiers=list,
    distclass=type,
    script_name=str,
    script_args=list,
    options=dict,
    license=str,
    keywords=(str, list),
    platforms=(str, list),
    cmdclass=dict,
    data_files=list,
    package_dir=str,
    package_data=dict,
    requires=list,
    provides=list,
    obsoletes=list
)


def setup_vars(varmap, autodiscover=True, force_manifest_in=False):
    """Return dict of keyword arguments for distutils setup function.
    
    Normally the ``varmap`` argument will be the ``globals()``
    of your setup script. The dictionary returned by this function
    is filtered to only include valid setup arguments, so you can
    safely pass your module globals without worrying about extra
    variables declared there.
    
    The ``autodiscover`` argument determines whether arguments
    not explicitly declared in ``varmap`` will be auto-discovered
    using the sub-functions above. For many use cases this will
    be sufficient; however, if you want finer control over what
    is auto-discovered, this argument can be set to ``False``
    and the sub-functions can be used individually (or setup
    arguments can be declared by hand).
    
    The ``force_manifest_in`` argument determines whether a
    ``MANIFEST.in`` template is generated even if you do not
    have a ``MANIFEST.in.in`` template. The chief reason for
    doing this would be to ensure that ``setuputils.py`` is
    included in your distributions. However, in most cases it
    is easier to either have a ``MANIFEST.in.in`` template,
    even an empty one, or to hand-generate your own ``MANIFEST``
    file (which is rarely done since it requires you to include
    *everything* by hand). Note that if you write your own
    ``MANIFEST.in`` file (and leave ``force_manifest_in`` at
    its default), you should be aware of the Python distutils'
    inconsistency about including files implied by the
    ``package_data``, ``data_files``, and ``scripts`` setup
    arguments (see docstrings above), and you must also include
    ``setuputils.py`` yourself.
    """
    
    varmap = dict(varmap)  # so we don't mutate the original
    
    if 'name' not in varmap:
        raise ValueError("You must supply a program name.")
    
    if autodiscover:
        add_vars(varmap)
        convert_lists(varmap)
        add_classifiers(varmap)
        autodiscover_all(varmap)
    
    if force_manifest_in or os.path.isfile("MANIFEST.in.in"):
        make_manifest_in(varmap)
    
    return dict(
        (k, v) for k, v in varmap.items()
        if k in distutils_keywords
    )
