"""Tests for the declarative method registry and registry-derived planning."""

from uncertainties import ufloat

from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine
from snowpyt_mechparams.execution.executor import PathwayExecutor
from snowpyt_mechparams.execution.planner import ExecutionPlanner
from snowpyt_mechparams.graph import build_graph, default_graph
from snowpyt_mechparams.methods import (
    MethodRegistry,
    MethodSpec,
    ParameterLevel,
    default_registry,
)
from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.pathway import find_parameterizations


def test_default_registry_has_one_spec_per_method_key():
    """Each built-in method should have one unambiguous spec."""
    registry = default_registry()
    keys = [(spec.target, spec.method_name) for spec in registry.all()]

    assert len(keys) == len(set(keys))


def test_graph_method_edges_match_registry_specs():
    """Generated method edges should be exactly the registered method specs."""
    registry = default_registry()
    graph = build_graph(registry)

    registry_keys = set()
    for spec in registry.all():
        registry_keys.add((spec.target, spec.method_name))
    graph_keys = {
        (edge.end.parameter, edge.method_name)
        for edge in graph.edges
        if edge.method_name is not None
    }

    assert graph_keys == registry_keys


def test_registry_generated_graph_preserves_pathway_counts():
    """Registry refactor should preserve public pathway counts."""
    expected_counts = {
        "density": 4,
        "elastic_modulus": 16,
        "poissons_ratio": 5,
        "shear_modulus": 32,
        "A11": 32,
        "B11": 32,
        "D11": 32,
        "A55": 32,
        "slab_weight": 4,
        "slab_weight_shear": 4,
        "slab_weight_shear_with_elasticity": 32,
    }

    for target, expected in expected_counts.items():
        node = default_graph.get_node(target)
        assert node is not None
        assert len(find_parameterizations(default_graph, node)) == expected


def test_planner_uses_dependencies_instead_of_hard_coded_layer_order():
    """Layer order should come from specs, not names."""
    registry = MethodRegistry(
        [
            MethodSpec(
                target="a_after",
                method_name="from_z",
                level=ParameterLevel.LAYER,
                source_nodes=("z_base",),
                required_inputs=("z_base",),
                function=lambda z_base: z_base,
                output_attr="a_after",
            ),
            MethodSpec(
                target="z_base",
                method_name="from_measurement",
                level=ParameterLevel.LAYER,
                source_nodes=("measured_z",),
                required_inputs=("measured_z",),
                function=lambda measured_z: measured_z,
                output_attr="z_base",
            ),
        ]
    )
    planner = ExecutionPlanner(registry)

    methods = {"a_after": "from_z", "z_base": "from_measurement"}
    assert planner.layer_order(methods) == ["z_base", "a_after"]


def test_slab_weight_elasticity_reports_missing_layer_prerequisites():
    """Slab planner should compute prerequisites and flag missing E/nu."""
    executor = PathwayExecutor()
    slab = Slab(
        layers=[
            Layer(
                thickness=ufloat(30, 1),
                density_calculated=ufloat(250, 10),
            )
        ],
        angle=35,
    )

    traces = executor._execute_slab_calculations(
        slab,
        "slab_weight_shear_with_elasticity",
    )

    assert [trace.parameter for trace in traces] == [
        "slab_weight",
        "slab_weight_shear",
        "slab_weight_shear_with_elasticity",
    ]
    assert traces[0].success
    assert traces[1].success
    assert not traces[2].success
    assert "E on all layers" in traces[2].error
    assert "nu on all layers" in traces[2].error


def test_execution_does_not_mutate_source_slab_layers():
    """Computed pathway values should be isolated to result slab copies."""
    layer = Layer(thickness=ufloat(30, 1), density_measured=ufloat(250, 10))
    slab = Slab(layers=[layer], angle=35)

    results = ExecutionEngine().execute_all(
        slab,
        "density",
        config=ExecutionConfig(include_method_uncertainty=False),
    )
    successful = next(iter(results.get_successful_pathways().values()))

    assert slab.layers[0].density_calculated is None
    assert successful.slab.layers[0].density_calculated is not None
