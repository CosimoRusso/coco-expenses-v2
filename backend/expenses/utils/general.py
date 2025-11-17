from typing import Iterable, TypeVar, Callable

__all__ = ["find_first"]

T = TypeVar('T')

def find_first(iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    for item in iterable:
        if predicate(item):
            return item
    return None