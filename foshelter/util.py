# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Assorted helper and wrapper functions
"""

import os.path
import logging
import shutil
import argparse
import enum
import re

from . import orm


COPYRIGHT="""
Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""

# https://stackoverflow.com/a/9283563/624066
_sepcamel = re.compile(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))')




class FSException(Exception):
    """
    Exception with errno and %-formatting for args (like logging module).

    All modules in this package should throw this for business-logic, expected
    and handled custom exceptions
    """
    def __init__(self, msg:str="", *args, errno:int=0):
        super().__init__(msg % args)
        self.errno = errno


class FSEnum(orm.Entity, enum.Enum):
    """Enum with custom str(): MyNEWClass.FOO_BAR -> 'My NEW Class: Foo Bar'"""
    def __str__(self):
        if not getattr(self, '_strname', None):
            self._strname = ": ".join(
                (re.sub(_sepcamel, r' \1', self.__class__.__name__),
                 self._name_.replace('_', ' ').title())
             )
        return self._strname

    def __repr__(self):
        return "<%s.%s>" % (
            self.__class__.__name__, self._name_)




def setup_logging(level:int=logging.DEBUG):
    """Consistency wrapper when package modules are run as scripts"""
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


def savename(slot: int) -> str:
    """Return a save game file name"""
    return 'Vault{0}.sav'.format(slot)


def localpath(slot: int, path: str = None) -> str:
    """
    Return the (local) full path for a save game file.

    If `path` is blank or a directory, join it with the default game save file
    name determined by `slot`, such as 'Vault1.sav'. Else use it as full file
    and path name. As such, a blank `path` effectively means current directory
    """
    if not path or os.path.isdir(path):
        return os.path.join(path or "", savename(slot))

    return path


def copy_file(source: str, target: str) -> str:
    """Consistency wrapper for local file copy operations"""
    #TODO: preserve timestamp (mtime) ONLY, not permissions/owner/group
    return shutil.copy2(source, target)


class ArgumentParser(argparse.ArgumentParser):
    """Consistency wrapper for argparse initialization"""
    def __init__(self, description: str, **kwargs):
        super().__init__(
            description=description,  # should be caller's module.__doc__
            epilog=COPYRIGHT,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **kwargs
        )
        group = self.add_mutually_exclusive_group()
        group.add_argument('-q', '--quiet',
                           dest='loglevel',
                           const=logging.WARNING,
                           default=logging.INFO,
                           action="store_const",
                           help="Suppress informative messages.")
        group.add_argument('-v', '--verbose',
                           dest='loglevel',
                           const=logging.DEBUG,
                           action="store_const",
                           help="Verbose mode, output extra info.")

    def parse_args(self, args=None, namespace=None):
        args = super().parse_args(args, namespace)
        args.debug = args.loglevel == logging.DEBUG
        return args
