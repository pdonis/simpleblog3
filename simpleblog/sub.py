#!/usr/bin/env python3
"""
Module SUB -- Simple Blog Sub-Package Handler
Package SIMPLEBLOG
Copyright (C) 2012-2013 by Peter A. Donis

Released under the GNU General Public License, Version 2
See the LICENSE and README files for more information
"""

from importlib import import_module

from plib.stdlib.classtools import first_subclass
from plib.stdlib.systools import tmp_sys_path


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


def load_sub(name, subtype, subdir, err, subcls):
    with tmp_sys_path(subdir):
        return load_submodule(subtype, subdir, name, err, subcls)


def load_subs(subs, subtype, subdir, err, subcls):
    with tmp_sys_path(subdir):
        for name in subs:
            yield load_submodule(subtype, subdir, name, err, subcls)
