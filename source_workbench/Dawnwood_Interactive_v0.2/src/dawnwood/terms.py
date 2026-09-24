"""Editable expression DAG. Node identity is content-based, not a frame counter."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Any

@dataclass(frozen=True)
class Ref:
    id: int

class Graph:
    def __init__(self) -> None:
        self.nodes: list[dict[str, Any]] = []
        self._intern: dict[str, Ref] = {}

    def _add(self, node: dict[str, Any]) -> Ref:
        content = dict(node)
        if 'args' in content:
            content['args'] = [self.nodes[i]['sha256'] for i in content['args']]
        raw = json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                         allow_nan=False).encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        if digest in self._intern:
            return self._intern[digest]
        ref = Ref(len(self.nodes))
        self.nodes.append({'id': ref.id, **node, 'sha256': digest})
        self._intern[digest] = ref
        return ref

    def literal(self, value: Any) -> Ref:
        # A JSON round-trip owns a copy of the expression supplied by the caller.
        value = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
        return self._add({'kind': 'literal', 'value': value})

    def symbol(self, name: str) -> Ref:
        return self._add({'kind': 'symbol', 'name': name})

    def call(self, head: str, *args: Ref) -> Ref:
        return self._add({'kind': 'call', 'head': head, 'args': [r.id for r in args]})

    def digest(self, ref: Ref) -> str:
        return self.nodes[ref.id]['sha256']

    def describe(self, ref: Ref) -> dict[str, Any]:
        return dict(self.nodes[ref.id])

    def to_json(self) -> list[dict[str, Any]]:
        return self.nodes

    @classmethod
    def from_json(cls, nodes: list[dict[str, Any]]) -> 'Graph':
        graph = cls()
        for row in nodes:
            payload = {k: v for k, v in row.items() if k not in ('id', 'sha256')}
            ref = graph._add(payload)
            if ref.id != row['id'] or graph.digest(ref) != row['sha256']:
                raise ValueError('Expression graph identity mismatch')
        return graph
