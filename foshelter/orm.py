# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ORM Wrapper for JSON objectification features
"""

import collections.abc


class Base:
    @classmethod
    def from_data(cls, data):
        return cls(data=data)

    def __init__(self, data=None, **kw):
        self._data = data
        assert not kw

    def to_data(self):
        return self._data


class Entity(Base):
    pass


class EntityList(Base, collections.abc.MutableSequence):
    """Base class for containers. Subclasses SHOULD override EntityClass"""
    EntityClass = Entity

    def __init__(self, data: list, **kw):
        super().__init__(data, **kw)
        self._list = [self.EntityClass(d) for d in self._data]

    def to_data(self):
        return [e.to_data() for e in self._list]

    # MutableSequence boilerplate

    def __getitem__(self, key):
        return self._list[key]

    def __setitem__(self, key, value: Entity):
        assert isinstance(value, self.EntityClass)
        self._list[key] = value
        self._data[key] = value.to_data()

    def __delitem__(self, key):
        del self._list[key]
        del self._data[key]

    def __len__(self):
        return len(self._list)

    def insert(self, idx, obj: Entity):
        assert isinstance(obj, self.EntityClass)
        self._list.insert(idx, obj)
        self._data.insert(idx, obj.to_data())
