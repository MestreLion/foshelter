# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Assorted helper and wrapper functions
"""

import logging


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
    """Wrapper for uniformity when package modules are run as scripts"""
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


def savename(vault: int) -> str:
    """Return a save game file name"""
    return 'Vault{0}.sav'.format(vault)
