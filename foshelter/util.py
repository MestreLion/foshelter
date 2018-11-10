# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Assorted helper and wrapper functions
"""

import logging


class FSException(Exception):
    pass


def basic_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(message)s')


def savename(vault: int) -> str:
    return 'Vault{0}.sav'.format(vault)
