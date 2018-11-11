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
from . import util


class Game(orm.RootEntity):
    """Root class for a game save"""

    @classmethod
    def from_save(cls, path, decrypted=False):
        with open(path, 'r') as fd:
            data = fd.read()

        if decrypted:
            try:
                return cls.from_data(json.loads(data))
            except json.decoder.JSONDecodeError as e:
                raise util.FSException('Could not load Vault data,'
                   ' is it a decrypted JSON file? %s: %s', path, e)

        try:
            return cls.from_data(savefile.decrypt(data))
        except ValueError as e:
            raise util.FSException('Could not load Vault data,'
               ' is it an encrypted SAV file? %s: %s', path, e)


    def __init__(self, data: dict, **kw):
        super().__init__(data, **kw)

        self.dwellers = dwellers.Dwellers.from_data(data['dwellers']['dwellers'], self)
