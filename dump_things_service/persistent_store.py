
# A persistent key-value store that uses strings as keys and values
# The disk representation is UTF-8 encoded Unicode, so it can be handled
# by git and similar text-affine tools.
#
# Each line in the disk file has one of the following two formats:
#
# + <key> <value>
# - <key>
#
# where <key> and <value> have whitespaces encoded with url-quote encoding.
#
# A line starting with a '+' indicates that the key-value pair was added to
# the store, while a line starting with a '-' indicates that the key was
# removed from the store.
#
# When the store is loaded, all lines are read and processed in order.
# This allows for fast store changes by merely appending
# lines to the end of the file.
#
# To compact the store, i.e., remove duplicate `+`-entries and remove
# `-`-entries, `PersistentStore.compact()` can be called. This will dump
# the current store to disk, leaving only unique `+`-entries in the file.
# Alternatively, the store can be compacted on initialization by passing
# `compact_db=True` to the constructor. In this case the store is loaded
# and immediately saved again, leaving only unique `+`-entries.
#
# It is safe to use this store from multiple threads.
#

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING
from urllib.parse import (
    quote_plus,
    unquote_plus,
)

if TYPE_CHECKING:
    from pathlib import Path


class PersistentStore:
    def __init__(self, path: Path, *, compact_db: bool = False):
        self.path = path
        self.lock = Lock()
        self.index: dict[str, str] = {}
        self.writer = self.path.open('at+', encoding='utf-8')
        self._load()
        if compact_db:
            self._save()

    def __del__(self):
        self.close()

    def __getitem__(self, key: str) -> str:
        if not isinstance(key, str):
            msg = f'Key must be a string, got {type(key)}'
            raise TypeError(msg)
        if key in self.index:
            return self.index[key]
        msg = f'Key {key} not found in persistent store at {self.path}'
        raise KeyError(msg)

    def __setitem__(self, key: str, value: str):
        if not isinstance(key, str):
            msg = f'Key must be a string, got {type(key)}'
            raise TypeError(msg)
        if not isinstance(value, str):
            msg = f'Key must be a string, got {type(key)}'
            raise TypeError(msg)
        self._add_item(key, value)

    def __delitem__(self, key):
        if not isinstance(key, str):
            msg = f'Key must be a string, got {type(key)}'
            raise TypeError(msg)
        if key in self.index:
            return self.remove_item(key)
        msg = f'Key {key} not found in persistent store at {self.path}'
        raise KeyError(msg)

    def __len__(self):
        return len(self.index)

    def items(self):
        return self.index.items()

    def values(self):
        return self.index.values()

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.index.get(key, default)

    def remove_item(self, key: str) -> bool:
        with self.lock:
            if key in self.index:
                del self.index[key]
                self._locked_remove_from_disk(key)
                return True
            return False

    def compact(self):
        with self.lock:
            self._locked_load()
            self._locked_save()

    def clear(self):
        with self.lock:
            self.index = {}
            self.writer.seek(0, 0)
            self.writer.truncate()
            self.writer.flush()

    def _add_item(self, key: str, value: str) -> bool:
        with self.lock:
            existing_value = self.index.get(key)
            if existing_value and existing_value == value:
                return False
            self.index[key] = value
            self._locked_add_to_disk(key, value)
            return True

    def _locked_add_to_disk(self, key: str, value: str):
        self.writer.write(f'+ {quote_plus(key)} {quote_plus(value)}\n')

    def _locked_remove_from_disk(self, key: str):
        self.writer.write(f'- {quote_plus(key)}\n')

    def close(self):
        self.writer.close()

    def _load(self):
        with self.lock:
            return self._locked_load()

    def _locked_load(self):
        index = {}
        self.writer.seek(0, 0)
        while True:
            line = self.writer.readline().strip()
            if line == '':
                break
            parts = line.split(' ')
            key = unquote_plus(parts[1])
            if parts[0] == '+':
                value = unquote_plus(parts[2])
                index[key] = value
            elif parts[0] == '-':
                if key in index:
                    del index[key]
            else:
                msg = f'Invalid line in index ({line}) in index file ({self.path})'
                raise RuntimeError(msg)
        self.index = index

    def _save(self):
        with self.lock:
            self._locked_save()

    def _locked_save(self):
        self.writer.seek(0, 0)
        self.writer.truncate()
        for key, value in self.index.items():
            self._locked_add_to_disk(key, value)
        self.writer.flush()
