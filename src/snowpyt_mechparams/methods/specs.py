"""Method metadata used to build graphs and dispatch calculations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Literal, Optional, Tuple


class ParameterLevel(Enum):
    """Whether a method computes one value per layer or one value per slab."""

    LAYER = "layer"
    SLAB = "slab"


CacheScope = Literal["none", "layer"]


@dataclass(frozen=True)
class MethodSpec:
    """Declarative description of one calculation method."""

    target: str
    method_name: str
    level: ParameterLevel
    source_nodes: Tuple[str, ...]
    required_inputs: Tuple[str, ...]
    function: Callable[..., Any]
    output_attr: str
    cache_scope: CacheScope = "none"
    description: str = ""
    citation: Optional[str] = None
