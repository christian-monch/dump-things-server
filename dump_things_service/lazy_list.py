""" Implementation of a lazy list

The lazy list calls a subclass method to generate list elements on demand. The
generation is based on the list index and information stored via
`add_info`. The list has as many entries as information entries were added
via `add_info`.

The lazy list is used to refer to large number of records with non-trivial
storage and retrieval costs. It is mainly used to efficiently implement
result pagination with `fastapi-pagination`.

"""
from __future__ import annotations

from abc import (
    abstractmethod,
    ABCMeta,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import (
        Any,
        Callable,
    )


class LazyList(list, metaclass=ABCMeta):

    class LazyListIterator:
        def __init__(self, lazy_list: LazyList):
            self.lazy_list = lazy_list
            self.index = 0

        def __iter__(self) -> LazyList.LazyListIterator:
            return self

        def __next__(self) -> str | dict:
            if self.index == len(self.lazy_list):
                raise StopIteration
            self.index += 1
            return self.lazy_list[self.index - 1]

    def __init__(self):
        super().__init__()
        self.list_info = []

    def __iter__(self) -> LazyList.LazyListIterator:
        return LazyList.LazyListIterator(self)

    def __len__(self) -> int:
        return len(self.list_info)

    def __getitem__(self, index: int) -> Any:
        if isinstance(index, slice):
            start = 0 if index.start is None else index.start
            stop = len(self) if index.stop is None else index.stop
            step = 1 if index.step is None else index.step

            # There is a condition in the list comprehension that ensures that
            # the indices are within bounds. We still adjust them here to
            # reduce the number of iterations in the list comprehension.
            if start < 0:
                start = max(len(self) + start, 0)
            elif start >= len(self):
                start = len(self) - 1

            if stop < 0:
                stop = max(len(self) + stop, -1)
            elif stop > len(self):
                stop = len(self)

            return [
                self.generate_element(i, self.list_info[i])
                for i in range(start, stop, step)
                if 0 <= i < len(self.list_info)
            ]

        return self.generate_element(index, self.list_info[index])

    @abstractmethod
    def generate_element(self, index: int, info: Any) -> Any:
        """
        Generate the list element at the specified index, using stored `info`

        This method should be implemented by subclasses to retrieve the content
        of the record at the given index. The generation is usually based on the
        `index` and the `info` object stored that was previously stored via
        `add_info`.

        :param index: The index of the record to retrieve.
        :param info: The object stored at the specified index in the info list.
        :return: The full element at the specified index, usually generated using
            `index` and `info`.
        """
        raise NotImplementedError

    def unique_identifier(self, info: Any) -> Any:
        """
        Return a unique identifier for the represented information

        The unique identifier is used in priority lists to uniquely identify an
        object across multiple lists.

        This should be implemented if the list is supposed to be used in a
        priority list.

        :param info: The surrogate information.
        :return: A unique identifier for the element represented by the surrogate.
        """
        raise NotImplementedError

    def sort_key(self, info: Any) -> str:
        """
        Return a string that can be used for sorting the list.

        This should be implemented if the list is supposed to be sorted.

        :param info: The surrogate information.
        :return: The string that should be used for sorting the list.
        """
        raise NotImplementedError

    def add_info(
        self,
        info: Iterable[Any],
    ) -> LazyList:
        """
        Add list entry information to the list.

        :param info: An iterable that contains information that `get_element`
        can use to lazily generate a list element.
        """
        self.list_info.extend(info)
        return self

    def sort(
        self,
        *,
        key: Callable | None = None,
        reverse: bool = False,
    ) -> LazyList:
        """
        Sort the lazy list based on a key function.
        """
        self.list_info.sort(key=key, reverse=reverse)
        return self

    def get_key_function(self) -> Callable:
        """
        Get the key function used to sort the list.

        This method should be implemented by subclasses to return a function
        that can be used to extract a key from the list info for sorting.
        """
        raise NotImplementedError("Subclasses must implement get_key_function")


class PriorityList(LazyList):
    """
    A lazy list that emits every item, identified by `key` only once.

    All lists should be added before the first iteration. All lists should be
    of the same type, i.e., they should all be `RecordDirList`s or all be
    `SQLList`s.
    """
    def __init__(
        self,
    ):
        super().__init__()
        self.seen = set()
        self.type = None

    def add_list(
        self,
        input_list: LazyList,
    ) -> PriorityList:
        # Check the type
        if self.type:
            if not isinstance(input_list, self.type):
                raise TypeError(
                    f"Expected input_list of type {self.type}, "
                    f"got {type(input_list)}"
                )
        else:
            self.type = type(input_list)

        for info in input_list.list_info:
            criteria = input_list.unique_identifier(info)
            if criteria not in self.seen:
                self.seen.add(criteria)
                self.list_info.append((info, input_list))
        return self

    def generate_element(self, index: int, info: Any) -> Any:
        # Delegate the generation to the input list
        return info[1].generate_element(index, info[0])

    def sort_key(self, info: Any) -> str:
        # Delegate the sort key to the input list
        return info[1].sort_key(info[0])


class ModifierList(LazyList):
    """
    A lazy list that modifies every item of inconing list by the `modifier`
    """
    def __init__(
            self,
            input_list: LazyList,
            modifier: Callable,
    ):
        super().__init__()
        self.input_list = input_list
        self.modifier = modifier
        self.list_info = input_list.list_info

    def generate_element(self, index: int, info: Any) -> Any:
        return self.modifier(self.input_list.generate_element(index, info))
