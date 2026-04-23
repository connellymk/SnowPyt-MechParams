"""
Tests for ExecutionEngine.execute_single and list_available_pathways.

These methods allow targeted single-pathway execution and pathway
enumeration without execution. They complement execute_all().
"""

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.execution import ExecutionEngine, ExecutionConfig
from snowpyt_mechparams.execution.results import PathwayResult
from snowpyt_mechparams.graph import graph


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def slab():
    """Minimal single-layer slab with data for density calculation."""
    layer = Layer(
        thickness=ufloat(30, 1),
        grain_form="RG",
        hand_hardness="1F",
        grain_size_avg=ufloat(0.5, 0.05),
        density_measured=ufloat(250, 15),
    )
    return Slab(layers=[layer], angle=35)


@pytest.fixture
def engine():
    return ExecutionEngine(graph)


# ---------------------------------------------------------------------------
# execute_single
# ---------------------------------------------------------------------------

class TestExecuteSingle:
    """Tests for ExecutionEngine.execute_single."""

    def test_returns_pathway_result_for_valid_methods(self, engine, slab):
        """execute_single should return a PathwayResult for a valid method dict."""
        result = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer"},
        )
        assert result is not None
        assert isinstance(result, PathwayResult)

    def test_pathway_succeeds_for_valid_methods(self, engine, slab):
        """The returned PathwayResult should report success."""
        result = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer"},
        )
        assert result is not None
        assert result.success

    def test_result_has_correct_methods_used(self, engine, slab):
        """methods_used on the result should match the requested method."""
        result = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer"},
        )
        assert result is not None
        assert result.methods_used.get("density") == "geldsetzer"

    def test_returns_none_for_nonexistent_method(self, engine, slab):
        """execute_single should return None when no pathway uses the given method."""
        result = engine.execute_single(
            slab,
            "density",
            {"density": "nonexistent_method"},
        )
        assert result is None

    def test_returns_none_when_method_does_not_match_target(self, engine, slab):
        """Requesting a method for a parameter not in the target's pathway returns None."""
        # elastic_modulus is not part of a density-only pathway
        result = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer", "elastic_modulus": "bergfeld"},
        )
        # The density pathway does not include elastic_modulus — no match
        assert result is None

    def test_raises_for_unknown_target_parameter(self, engine, slab):
        """execute_single should raise ValueError for an unknown target."""
        with pytest.raises(ValueError, match="Unknown target parameter"):
            engine.execute_single(slab, "not_a_real_parameter", {"density": "geldsetzer"})

    def test_executes_correct_method_not_others(self, engine, slab):
        """Only the requested method should be recorded, not alternatives."""
        result_kim = engine.execute_single(
            slab,
            "density",
            {"density": "kim_jamieson_table2"},
        )
        assert result_kim is not None
        assert result_kim.methods_used.get("density") == "kim_jamieson_table2"
        # Should differ from the geldsetzer result
        result_gel = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer"},
        )
        assert result_gel is not None
        density_kim = result_kim.slab.layers[0].density_calculated
        density_gel = result_gel.slab.layers[0].density_calculated
        # Both should be set but may differ in value
        assert density_kim is not None
        assert density_gel is not None

    def test_accepts_optional_config(self, engine, slab):
        """execute_single should accept and respect an ExecutionConfig."""
        config = ExecutionConfig(verbose=False, include_method_uncertainty=False)
        result = engine.execute_single(
            slab,
            "density",
            {"density": "geldsetzer"},
            config=config,
        )
        assert result is not None
        assert result.success

    def test_original_slab_not_mutated(self, engine, slab):
        """execute_single should not modify the input slab."""
        original_density = slab.layers[0].density_calculated  # None before execution

        engine.execute_single(slab, "density", {"density": "geldsetzer"})

        assert slab.layers[0].density_calculated == original_density

    def test_slab_weight_does_not_fallback_to_measured_density_after_method_failure(self, engine):
        """Failed empirical density pathways must not compute W from measured density."""
        layer = Layer(
            thickness=ufloat(10, 0.5),
            density_measured=ufloat(200, 10),
            grain_form="RG",
            # Missing hand_hardness: empirical density methods should fail.
        )
        slab = Slab(layers=[layer], angle=30)

        results = engine.execute_all(slab, "slab_weight")

        assert results.total_pathways == 4
        for pathway in results.pathways.values():
            density_method = pathway.methods_used["density"]
            density_traces = pathway.get_traces_for_parameter("density")
            slab_weight_trace = pathway.get_traces_for_parameter("slab_weight")[-1]

            if density_method == "data_flow":
                assert density_traces[0].success
                assert pathway.success
                assert slab_weight_trace.success
            else:
                assert not density_traces[0].success
                assert not pathway.success
                assert not slab_weight_trace.success
                assert "computed density" in slab_weight_trace.error


# ---------------------------------------------------------------------------
# list_available_pathways
# ---------------------------------------------------------------------------

class TestListAvailablePathways:
    """Tests for ExecutionEngine.list_available_pathways."""

    def test_returns_list(self, engine):
        """list_available_pathways should return a list."""
        pathways = engine.list_available_pathways("density")
        assert isinstance(pathways, list)

    def test_each_entry_has_required_keys(self, engine):
        """Every pathway dict should have 'id', 'description', and 'methods' keys."""
        pathways = engine.list_available_pathways("density")
        assert len(pathways) > 0
        for entry in pathways:
            assert "id" in entry
            assert "description" in entry
            assert "methods" in entry

    def test_methods_value_is_dict(self, engine):
        """The 'methods' value in each entry should be a dict."""
        pathways = engine.list_available_pathways("density")
        for entry in pathways:
            assert isinstance(entry["methods"], dict)

    def test_pathway_ids_are_unique(self, engine):
        """No two pathways should share the same id."""
        pathways = engine.list_available_pathways("density")
        ids = [p["id"] for p in pathways]
        assert len(ids) == len(set(ids)), "Duplicate pathway IDs found"

    def test_pathway_count_matches_execute_all(self, engine, slab):
        """Pathway count from list_available_pathways should match execute_all total."""
        listed = engine.list_available_pathways("density")
        results = engine.execute_all(slab, "density")
        assert len(listed) == results.total_pathways

    def test_density_pathways_include_density_method(self, engine):
        """All density pathways should have 'density' in their methods dict."""
        pathways = engine.list_available_pathways("density")
        for entry in pathways:
            assert "density" in entry["methods"]

    def test_descriptions_are_strings(self, engine):
        """Pathway descriptions should be non-empty strings."""
        pathways = engine.list_available_pathways("density")
        for entry in pathways:
            assert isinstance(entry["description"], str)
            assert len(entry["description"]) > 0

    def test_raises_for_unknown_target(self, engine):
        """list_available_pathways should raise ValueError for an unknown target."""
        with pytest.raises(ValueError, match="Unknown target parameter"):
            engine.list_available_pathways("not_a_real_parameter")

    def test_elastic_modulus_pathways_use_known_methods(self, engine):
        """Elastic modulus pathways should reference one of the known E methods."""
        known_e_methods = {"bergfeld", "kochle", "wautier", "schottner"}
        pathways = engine.list_available_pathways("elastic_modulus")
        for entry in pathways:
            assert entry["methods"].get("elastic_modulus") in known_e_methods
