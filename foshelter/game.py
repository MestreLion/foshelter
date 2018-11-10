# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Top level game classes
"""

import json

from . import orm
from . import dwellers
from . import savefile

class Game(orm.Entity):
    """Root class for a game save"""

    @classmethod
    def from_save(cls, path, decrypted=False):
        with open(path, 'r') as fd:
            data = json.load(fd) if decrypted else savefile.decrypt(fd.read())
        return cls.from_data(data)

    def __init__(self, data: dict, **kw):
        super().__init__(data, **kw)

        self.dwellers = dwellers.Dwellers.from_data(data['dwellers']['dwellers'])
