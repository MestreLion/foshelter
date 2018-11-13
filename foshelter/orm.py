# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ORM Wrapper for JSON objectification features
"""

import collections.abc


class Base:
    @classmethod
    def from_data(cls, data, root=None):
        return cls(data, root)

    def __init__(self, data, root=None):
        self._data = data
        self._root = root
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
        return cls(data)


class EntityList(Base, collections.abc.MutableSequence):
    """Base class for containers. Subclasses SHOULD override EntityClass"""
    EntityClass = Entity

    @classmethod
    def _item_data(cls, item):
        return item.to_data() if issubclass(cls.EntityClass, Base) else item

    def __init__(self, data: list, root=None):
        super().__init__(data, root)
        self._list = [self.EntityClass(d, root)
                      if issubclass(self.EntityClass, Base)
                      else self.EntityClass(d)
                      for d in self._data]

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

    def __getitem__(self, idx: int or slice):
        if isinstance(idx, int):
            return self._list[idx]
        elif isinstance(idx, slice):
            return  self.__class__((_ for _ in self._data[idx]), self._root)
            #return self.__class__((_.to_data() for _ in self._list[idx]), root=self._root)
        raise TypeError("%s indices must be integers or slices, not %s".
                        format(self.__class__.__name__, type(idx)))

    def __setitem__(self, idx: int or slice, obj: Entity or EntityList):
        if not isinstance(idx, (int, slice)):
            raise TypeError("%s indices must be integers or slices, not %s".
                            format(self.__class__.__name__, type(idx)))
        assert isinstance(obj, (self.EntityClass, self.__class__))
        self._list[idx] = obj
        self._data[idx] = self._item_data(obj)

    def __delitem__(self, idx: int or slice):
        if not isinstance(idx, (int, slice)):
            raise TypeError("%s indices must be integers or slices, not %s".
                            format(self.__class__.__name__, type(idx)))
        del self._list[idx]
        del self._data[idx]

    def __len__(self):
        assert len(self._list) == len(self._data)
        return len(self._list)

    def insert(self, idx: int, obj: Entity):
        assert isinstance(obj, self.EntityClass)
        self._list.insert(idx, obj)
        self._data.insert(idx, self._item_data(obj))
