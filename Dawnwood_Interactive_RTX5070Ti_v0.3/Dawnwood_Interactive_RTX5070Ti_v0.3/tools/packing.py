#!/usr/bin/env python3
"""Arithmetic planner, not a measurement of the GPU. Units are explicitly MiB."""
import argparse
import json
import math


def plan(free_mib: int, reserve_mib: int, fill: float, side: int, codec: str,
         active: int = 65536) -> dict:
    if free_mib < 0 or reserve_mib < 0 or not 0 < fill <= 1 or side < 4 or side % 4 or active < 1:
        raise ValueError('Invalid planner input')
    free = free_mib * 2**20
    budget = max(0, min(free - reserve_mib * 2**20, math.floor(free * fill)))
    texture = side**2 * (1 if codec == 'bc5' else 2)
    aux = (side // 4)**2 * 8
    descriptor = 24
    pages = budget // (texture + aux + descriptor)
    blocks = pages * (side // 4)**2
    return {'kind': 'arithmetic_only', 'free_bytes_after_hot_and_staging': free,
            'reserve_bytes': reserve_mib * 2**20, 'fill': fill, 'budget_bytes': budget,
            'codec': codec, 'side': side, 'pages_before_array_padding': pages,
            'texture_bytes_per_page': texture, 'aux_bytes_per_page': aux,
            'descriptor_bytes_per_page': descriptor, 'token_pairs': blocks * 16,
            'payload_bytes': pages * (texture + aux),
            'intervals_to_visit_every_block_once': (blocks + active - 1) // active,
            'note': 'Driver/array padding and other GPU users may reduce the allocated count.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--free-mib', type=int, required=True)
    p.add_argument('--reserve-mib', type=int, default=512)
    p.add_argument('--fill', type=float, default=.96)
    p.add_argument('--side', type=int, default=4096)
    p.add_argument('--codec', choices=['bc5', 'rg8'], default='bc5')
    p.add_argument('--active', type=int, default=65536)
    a = p.parse_args()
    print(json.dumps(plan(a.free_mib, a.reserve_mib, a.fill, a.side, a.codec, a.active), indent=2))
