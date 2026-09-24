"""Concrete integer relations appearing in the source's parity and array notation."""
from __future__ import annotations
from collections.abc import Iterable

def bit(value: int) -> int:
    if type(value) is not int or value not in (0, 1):
        raise ValueError('A one-bit value is 0 or 1')
    return value

def parity(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('Population parity uses a nonnegative integer')
    return value.bit_count() & 1

def even_odd(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('Even/odd notation uses a nonnegative integer')
    return value & 1

def child(index: int, branch: int) -> int:
    if type(index) is not int or index < 0:
        raise ValueError('An implicit tree index is a nonnegative integer')
    return 2 * index + 1 + bit(branch)

def route(bits: Iterable[int], reversal: int = 0) -> tuple[int, list[int]]:
    reversal = bit(reversal)
    index, indices = 0, [0]
    for direction in bits:
        index = child(index, bit(direction) ^ reversal)
        indices.append(index)
    return index, indices
