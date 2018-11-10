# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Assorted helper and wrapper functions
"""

import os.path
import logging
import shutil


class FSException(Exception):
    """
    Exception with errno and %-formatting for args (like logging module).

    All modules in this package should throw this for business-logic, expected
    and handled custom exceptions
    """
    def __init__(self, msg:str="", *args, errno:int=0):
        super().__init__(msg % args)
        self.errno = errno


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
