from simpy.core import BoundClass
from simpy.resources.store import StorePut, StoreGet, Store
from bisect import insort
from sys import maxsize

class IndexedOrderedStoreGet(StoreGet):
    """Request to get *items* from the store at *indices*. The default
    *indices* returns the item at index 0 to behave exactly like
    :class:`StoreGet`.

    """
    def __init__(self, resource, indices=[0]):
        self.indices = indices
        super(IndexedOrderedStoreGet, self).__init__(resource)

class IndexedOrderedStore(Store):
    """Resource with *capacity* slots for storing objects in order and
    retrieving multiple items simultaneously from arbitrary positions in the
    :class:`IndexedOrderedStore`. All items in an *IndexedOrderedStore*
    instance must be orderable, which is to say that items must implement
    :meth:`~object.__lt__()`.

    """

    put = BoundClass(StorePut)
    """Request to put an *item* into the store."""

    get = BoundClass(IndexedOrderedStoreGet)
    """Request to get *items* at *indices* out of the store."""

    def _do_put(self, event):
        if len(self.items) < self._capacity:
            insort(self.items, event.item)
            event.succeed()

    def _do_get(self, event):
        if len(event.indices) == 1:
            event.succeed([self.items.pop(event.indices[0])])
            return

        result = []

        for idx, val in enumerate(event.indices):
            result.append(self.items[val])
            self.items[val] = self.items[-1-idx]

        if len(event.indices) > 0:
            del self.items[-len(event.indices):]
            self.items.sort()

        event.succeed(result)

class Docket(IndexedOrderedStore):
    """Resource with infinite capacity for storing appeals, objects with
    attributes that include *priority*, whether the appeal should be
    prioritized, and *judge*, whether the appeal is tied to a specific judge.
    The appeals must also be orderable, which is to say they must implement
    :meth:`~object.__lt__()`.

    """
    def __init__(self, env):
        super(Docket, self).__init__(env)

        self.priority_store = IndexedOrderedStore(env)
        """Substore of items for which priority is truthy."""

    def prepopulate(self, items):
        """Replace the store's contents with *items*."""
        if len(items) > self._capacity:
            return False

        self.items, self.priority_store.items = [], []

        for item in items:
            if item.priority:
                self.priority_store.items.append(item)
            else:
                self.items.append(item)

        self.items.sort()
        self.priority_store.items.sort()

        return True

    def nonpriority_count(self):
        """The number of nonpriority items in the store."""
        return len(self.items)

    def priority_count(self):
        """The number of priority items in the store."""
        return len(self.priority_store.items)

    def count(self):
        """The total number of items in the store."""
        return self.nonpriority_count() + self.priority_count()

    def get_priority_appeals(self, judge = None, limit = maxsize):
        """Request to get appeals from the docket where priority is truthy.

        Args:
            judge: Obtain appeals tied to a specific judge. Can be a list of
                judges. Defaults to None.
            limit: The maximum number of appeals to return. Defaults to all.

        """
        if not isinstance(judge, list):
            judge = [judge]

        indices = [idx for idx, item in enumerate(self.priority_store.items)
                   if item.judge in judge]
        return self.priority_store.get(indices[:limit])

    def get_nonpriority_appeals(self, judge = None, limit = maxsize, range = maxsize):
        """Request to get appeals from the docket where priority is falsey.

        Args:
            judge: Obtain appeals tied to a specific judge. Can be a list of
                judges. Defaults to None.
            limit: The maximum number of appeals to return. Defaults to all.
            range: The maximum depth to search the docket for matching appeals.
                Defaults to all.

        """
        if not isinstance(judge, list):
            judge = [judge]

        indices = [idx for idx, item in enumerate(self.items[:range])
                   if item.judge in judge]
        return self.get(indices[:limit])

    def _do_put(self, event):
        if self.count() < self._capacity:
            if event.item.priority:
                self.priority_store._do_put(event)
            else:
                super(Docket, self)._do_put(event)
