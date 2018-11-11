# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ORM Wrapper for JSON objectification features
"""

import collections.abc


class Base:
    @classmethod
    def from_data(cls, data, root):
        return cls(data=data, root=root)

    def __init__(self, data=None, root=None, **kw):
        self._data = data
        self._root = root
        assert not kw
        assert not root or isinstance(root, RootEntity)

    def to_data(self):
        return self._data


class Entity(Base):
    def __str__(self):
        return '\n'.join('{0}: {1}'.format(k.capitalize(), v)
                         for k, v in vars(self).items())


class RootEntity(Entity):
    @classmethod
    def from_data(cls, data):
        return cls(data=data)


class EntityList(Base, collections.abc.MutableSequence):
    """Base class for containers. Subclasses SHOULD override EntityClass"""
    EntityClass = Entity

    def __init__(self, data: list, **kw):
        super().__init__(data, **kw)
        self._list = [self.EntityClass(d) for d in self._data]

    def get(self, ID: int, default):
        for e in self._list:
            if getattr(e, 'ID', None) == ID:
                return e
        return default

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return repr(self._list)

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
