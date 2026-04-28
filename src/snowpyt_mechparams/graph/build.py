"""Build parameter graphs from method registry metadata."""

from __future__ import annotations

from typing import Iterable

from snowpyt_mechparams.graph.structures import Graph, GraphBuilder, Node
from snowpyt_mechparams.methods import MethodRegistry, default_registry
from snowpyt_mechparams.methods.specs import ParameterLevel

MEASURED_NODES = (
    "measured_density",
    "measured_hand_hardness",
    "measured_grain_form",
    "measured_grain_size",
    "measured_layer_thickness",
    "measured_layer_location",
    "measured_slope_angle",
)


def build_graph(registry: MethodRegistry | None = None) -> Graph:
    """Build a parameter dependency graph from a method registry."""
    registry = registry or default_registry()
    builder = GraphBuilder()

    snow_pit = builder.param("snow_pit")
    for measured in MEASURED_NODES:
        builder.flow(snow_pit, builder.param(measured))

    for spec in registry.all():
        builder.param(spec.target, level=spec.level.value)

    for spec in registry.all():
        target = builder.param(spec.target, level=spec.level.value)
        sources = []
        for name in spec.source_nodes:
            sources.append(_ensure_parameter(builder, name, registry))
        if len(sources) == 1:
            builder.method_edge(sources[0], target, spec.method_name)
        else:
            merge = builder.merge(_merge_name(spec.source_nodes))
            for source in sources:
                builder.flow(source, merge)
            builder.method_edge(merge, target, spec.method_name)

    return builder.build()


def _ensure_parameter(
    builder: GraphBuilder, name: str, registry: MethodRegistry
) -> Node:
    """Create or retrieve a parameter node with registry level metadata."""
    target_specs = registry.methods_for(name)
    if target_specs:
        return builder.param(name, level=target_specs[0].level.value)
    return builder.param(name)


def _merge_name(source_nodes: Iterable[str]) -> str:
    """Return a stable merge-node name for an input combination."""
    parts = []
    for node in source_nodes:
        parts.append(node.removeprefix("measured_"))
    return "merge_" + "_".join(parts)


def target_names_by_level(  # noqa: E501
    graph: Graph, level: ParameterLevel
) -> frozenset[str]:
    """Return target names by graph node level."""
    return frozenset(
        node.parameter for node in graph.nodes if node.level == level.value
    )
