"""Utility functions for lpy_autocomplete."""

import functools
import itertools
from collections.abc import Callable, Iterable, Iterator
from typing import Any, TypeVar

T = TypeVar("T")


def mangle(s: str) -> str:
    """Convert lispy symbol to Python identifier.

    In lispython, this just converts hyphens to underscores.
    """
    if not s:
        return ""
    return s.replace("-", "_")


def unmangle(s: str) -> str:
    """Convert Python identifier to lispy symbol.

    In lispython, this converts underscores to hyphens,
    but preserves leading and trailing underscores (e.g., __call__, _private).
    """
    if not s:
        return ""

    # Count and strip leading underscores
    leading = len(s) - len(s.lstrip("_"))
    # Count and strip trailing underscores
    trailing = len(s) - len(s.rstrip("_"))

    # Handle all-underscore strings
    if leading + trailing >= len(s):
        return s

    # Extract middle part and convert
    middle = s[leading : len(s) - trailing if trailing else None]
    middle = middle.replace("_", "-")

    return "_" * leading + middle + "_" * trailing


def is_none(x: Any) -> bool:
    """Check if x is None."""
    return x is None


def is_string(x: Any) -> bool:
    """Check if x is a string."""
    return isinstance(x, str)


def first(coll: Iterable[T]) -> T | None:
    """Return first item from collection."""
    return next(iter(coll), None)


def last(coll: Iterable[T]) -> T:
    """Return last item from collection."""
    return tuple(coll)[-1]


def drop(count: int, coll: Iterable[T]) -> Iterator[T]:
    """Drop count elements from coll and yield back the rest."""
    return itertools.islice(coll, count, None)


def drop_last(count: int, coll: Iterable[T]) -> list[T]:
    """Drop last count elements from collection."""
    lst = list(coll)
    return lst[:-count] if count > 0 else lst


def butlast(coll: Iterable[T]) -> list[T]:
    """Return all but the last element."""
    return drop_last(1, coll)


def allkeys(d: dict) -> tuple[str, ...]:
    """Get all keys from a possibly nested dict, flattened."""
    def _allkeys(d: Any, parents: tuple = ()) -> list:
        if isinstance(d, (list, tuple)):
            return []
        result = []
        for k, v in d.items():
            new_key = parents + (k,)
            if isinstance(v, dict):
                result.extend(_allkeys(v, new_key))
            else:
                result.append(new_key)
        return result

    return tuple(last(k) for k in _allkeys(d))


def juxt(*funcs: Callable) -> Callable:
    """Return a function that applies each func to args, collecting results."""
    def inner(*args, **kwargs):
        return [f(*args, **kwargs) for f in funcs]
    return inner


def flip(func: Callable) -> Callable:
    """Return a function with arguments flipped."""
    @functools.wraps(func)
    def flipped(*args, **kwargs):
        return func(*reversed(args), **kwargs)
    return flipped


# Re-exports from itertools/functools
chain = itertools.chain
islice = itertools.islice
reduce = functools.reduce
remove = itertools.filterfalse
repeat = itertools.repeat


def distinct(iterable: Iterable[T]) -> Iterator[T]:
    """Yield unique elements, preserving order."""
    seen: set = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


def flatten(iterables: Iterable[Iterable[T]]) -> Iterator[T]:
    """Flatten one level of nesting."""
    return itertools.chain.from_iterable(iterables)
