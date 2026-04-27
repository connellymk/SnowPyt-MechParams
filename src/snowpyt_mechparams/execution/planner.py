"""Registry-derived execution planning."""

from __future__ import annotations

from typing import Dict, List, Set

from snowpyt_mechparams.methods import MethodRegistry
from snowpyt_mechparams.methods.specs import ParameterLevel


class ExecutionPlanner:
    """Derive layer and slab execution order from registered dependencies."""

    def __init__(self, registry: MethodRegistry) -> None:
        self.registry = registry
        self.layer_targets = registry.targets_by_level(ParameterLevel.LAYER)
        self.slab_targets = registry.targets_by_level(ParameterLevel.SLAB)

    def layer_order(self, methods_used: Dict[str, str]) -> List[str]:
        """Return selected layer targets in dependency order."""
        selected = set(methods_used).intersection(self.layer_targets)
        ordered: List[str] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(parameter: str) -> None:
            if parameter in visited:
                return
            if parameter in visiting:
                msg = f"Cyclic layer dependency involving {parameter}"
                raise ValueError(msg)
            visiting.add(parameter)
            spec = self.registry.require(parameter, methods_used[parameter])
            for source in spec.source_nodes:
                if source in selected:
                    visit(source)
            visiting.remove(parameter)
            visited.add(parameter)
            ordered.append(parameter)

        for parameter in sorted(selected):
            visit(parameter)
        return ordered

    def slab_order(
        self, target_parameter: str, methods_used: Dict[str, str]
    ) -> List[str]:
        """Return selected slab targets needed to compute target_parameter."""
        selected = set(methods_used).intersection(self.slab_targets)
        if target_parameter not in selected:
            return []

        ordered: List[str] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(parameter: str) -> None:
            if parameter in visited:
                return
            if parameter in visiting:
                msg = f"Cyclic slab dependency involving {parameter}"
                raise ValueError(msg)
            visiting.add(parameter)
            spec = self.registry.require(parameter, methods_used[parameter])
            for source in spec.source_nodes:
                if source in selected:
                    visit(source)
            visiting.remove(parameter)
            visited.add(parameter)
            ordered.append(parameter)

        visit(target_parameter)
        return ordered
