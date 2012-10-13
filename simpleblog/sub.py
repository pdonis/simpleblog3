#!/usr/bin/env python
"""
Module SUB -- Simple Blog Sub-Package Handler
Package SIMPLEBLOG
Copyright (C) 2012 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

import sys
import os
from contextlib import contextmanager
from importlib import import_module


def first_subclass(o, c):
    """Return first object in o that is a subclass of c
    """
    return first(
        obj for obj in vars(o).itervalues()
        if (obj is not c)
        and isinstance(obj, type)
        and issubclass(obj, c)
    )


def load_submodule(subtype, subdir, name, err, subcls):
    name = name.replace('-', '_')
    mod = None
    if subdir:
        # User-supplied module takes precedence
        try:
            mod = import_module(name)
        except ImportError:
            pass
    if mod is None:
        try:
            mod = import_module("simpleblog.{0}s.{1}".format(subtype, name))
        except ImportError:
            raise err("{0} {1} not found!".format(subtype, name))
    klass = first_subclass(mod, subcls)
    if not klass:
        raise err("no {0} in {1} module!".format(subtype, name))
    return mod, klass


@contextmanager
def tmp_sys_path(subdir, index=0):
    """Temporarily munge ``sys.path`` to allow import from non-standard dir
    """
    
    if subdir:
        subdir = os.path.abspath(subdir)
        oldpath = sys.path[:]
        sys.path.insert(index, subdir)
    else:
        oldpath = None
    try:
        yield
    finally:
        if oldpath:
            sys.path[:] = oldpath


def load_sub(name, subtype, subdir, err, subcls):
    with tmp_sys_path(subdir):
        return load_submodule(subtype, subdir, name, err, subcls)


def load_subs(subs, subtype, subdir, err, subcls):
    with tmp_sys_path(subdir):
        for name in subs:
            yield load_submodule(subtype, subdir, name, err, subcls)
