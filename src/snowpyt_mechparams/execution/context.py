"""Per-pathway execution state isolated from source slabs."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterator, List, Tuple

from snowpyt_mechparams.models import Layer, Slab


class ExecutionContext:
    """Copy-on-write container for one pathway execution."""

    def __init__(self, source_slab: Slab, copy_layers: bool) -> None:
        self.source_slab = source_slab
        self.layers: List[Layer] = []
        for layer in source_slab.layers:
            self.layers.append(replace(layer) if copy_layers else layer)

    def iter_layers(self) -> Iterator[Tuple[int, Layer]]:
        """Yield working layers with their source index."""
        yield from enumerate(self.layers)

    def materialize(self) -> Slab:
        """Return a result slab with the pathway's working layers."""
        return replace(self.source_slab, layers=self.layers)
