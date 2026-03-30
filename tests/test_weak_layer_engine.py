"""
Tests for the execution engine's handling of weak-layer and stability parameters.

Tests cover:
- Weak-layer parameter calculation (no WEAC required)
- Dispatcher registration of new ParameterLevel values
- Execution engine targeting G_c, G_Ic, g_delta
- Integration: full pipeline from slab → g_delta (requires weac)
"""

from __future__ import annotations

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.models.weak_layer import WeakLayer
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, ParameterLevel
from conftest import requires_weac

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_slab_for_stability() -> Slab:
    """
    Build a minimal ``Slab`` with all fields needed to run the full stability
    pipeline (density → E/ν/G → weak-layer params → g_delta).

    All mechanical parameters are pre-populated (density_calculated etc.) so
    the executor can skip layer-param computation if it isn't the target.
    """
    layer = Layer(
        thickness=ufloat(20.0, 0.0),
        grain_form="RG",
        density_calculated=ufloat(250.0, 0.0),
        elastic_modulus=ufloat(5.0, 0.0),
        poissons_ratio=ufloat(0.2, 0.0),
        shear_modulus=ufloat(2.0, 0.0),
    )
    weak_layer = WeakLayer(
        thickness=ufloat(3.0, 0.0),
        density_measured=ufloat(150.0, 0.0),
    )
    return Slab(
        layers=[layer],
        angle=ufloat(35.0, 0.0),
        weak_layer=weak_layer,
    )


# ---------------------------------------------------------------------------
# ParameterLevel enum
# ---------------------------------------------------------------------------

class TestParameterLevel:
    """Verify the new ParameterLevel enum values exist."""

    def test_weak_layer_enum_value(self):
        assert ParameterLevel.WEAK_LAYER.value == "weak_layer"

    def test_stability_enum_value(self):
        assert ParameterLevel.STABILITY.value == "stability_model"

    def test_all_four_levels_present(self):
        levels = {e.value for e in ParameterLevel}
        assert "layer" in levels
        assert "slab" in levels
        assert "weak_layer" in levels
        assert "stability_model" in levels


# ---------------------------------------------------------------------------
# Dispatcher — registration of weak-layer methods
# ---------------------------------------------------------------------------

class TestDispatcherWeakLayerMethods:
    """Verify weak-layer and stability methods are registered in the dispatcher."""

    def setup_method(self):
        self.dispatcher = MethodDispatcher()

    def test_G_c_method_registered(self):
        spec = self.dispatcher.get_method("G_c", "weissgraeber_rosendahl")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_G_Ic_method_registered(self):
        spec = self.dispatcher.get_method("G_Ic", "weissgraeber_rosendahl")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_G_IIc_method_registered(self):
        spec = self.dispatcher.get_method("G_IIc", "weissgraeber_rosendahl")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_sigma_c_method_registered(self):
        spec = self.dispatcher.get_method("sigma_c", "weissgraeber_rosendahl")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_tau_c_method_registered(self):
        spec = self.dispatcher.get_method("tau_c", "weissgraeber_rosendahl")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_sigma_comp_method_registered(self):
        spec = self.dispatcher.get_method("sigma_comp", "reiweger")
        assert spec is not None
        assert spec.level == ParameterLevel.WEAK_LAYER

    def test_g_delta_method_registered(self):
        spec = self.dispatcher.get_method("g_delta", "weac_skier")
        assert spec is not None
        assert spec.level == ParameterLevel.STABILITY


# ---------------------------------------------------------------------------
# Dispatcher — execute() for weak-layer constants
# ---------------------------------------------------------------------------

class TestDispatcherExecuteWeakLayer:
    """Verify the dispatcher's execute() returns correct reference constants."""

    def setup_method(self):
        self.dispatcher = MethodDispatcher()
        self.slab = _make_slab_for_stability()

    def _nominal(self, v):
        if hasattr(v, "nominal_value"):
            return float(v.nominal_value)
        return float(v)

    def test_execute_G_c_returns_1_0(self):
        value, error = self.dispatcher.execute("G_c", "weissgraeber_rosendahl", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(1.0)

    def test_execute_G_Ic_returns_0_56(self):
        value, error = self.dispatcher.execute("G_Ic", "weissgraeber_rosendahl", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(0.56)

    def test_execute_G_IIc_returns_0_79(self):
        value, error = self.dispatcher.execute("G_IIc", "weissgraeber_rosendahl", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(0.79)

    def test_execute_sigma_c_returns_6_16(self):
        value, error = self.dispatcher.execute("sigma_c", "weissgraeber_rosendahl", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(6.16)

    def test_execute_tau_c_returns_5_09(self):
        value, error = self.dispatcher.execute("tau_c", "weissgraeber_rosendahl", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(5.09)

    def test_execute_sigma_comp_returns_2_6(self):
        value, error = self.dispatcher.execute("sigma_comp", "reiweger", slab=self.slab)
        assert error is None
        assert value is not None
        assert self._nominal(value) == pytest.approx(2.6)

    def test_execute_weak_layer_returns_ufloat(self):
        """Weak-layer constants should be returned as UncertainValue (ufloat)."""
        import uncertainties
        value, _ = self.dispatcher.execute("G_Ic", "weissgraeber_rosendahl", slab=self.slab)
        assert isinstance(value, uncertainties.UFloat)

    def test_execute_requires_slab_for_weak_layer_method(self):
        """Weak-layer methods require a slab (API consistency)."""
        value, error = self.dispatcher.execute("G_Ic", "weissgraeber_rosendahl", slab=None)
        assert value is None
        assert error is not None


# ---------------------------------------------------------------------------
# Executor — _execute_weak_layer_calculations
# ---------------------------------------------------------------------------

class TestExecutorWeakLayerCalculations:
    """Unit tests for the executor's _execute_weak_layer_calculations helper."""

    def setup_method(self):
        from snowpyt_mechparams.execution.executor import PathwayExecutor
        self.executor = PathwayExecutor()
        self.slab = _make_slab_for_stability()

    def test_populates_weak_layer_on_slab(self):
        """After execution, slab.weak_layer should have G_Ic set."""
        assert self.slab.weak_layer.G_Ic is None
        params = {"G_Ic": "weissgraeber_rosendahl"}
        traces = self.executor._execute_weak_layer_calculations(self.slab, params)
        assert len(traces) == 1
        assert traces[0].success
        assert self.slab.weak_layer.G_Ic is not None

    def test_weak_layer_is_weaklayer_instance(self):
        """slab.weak_layer should be a WeakLayer instance."""
        assert isinstance(self.slab.weak_layer, WeakLayer)

    def test_all_six_params_populated(self):
        """All six weak-layer params should be set after a full execution."""
        params = {
            "G_c": "weissgraeber_rosendahl",
            "G_Ic": "weissgraeber_rosendahl",
            "G_IIc": "weissgraeber_rosendahl",
            "sigma_c": "weissgraeber_rosendahl",
            "tau_c": "weissgraeber_rosendahl",
            "sigma_comp": "reiweger",
        }
        traces = self.executor._execute_weak_layer_calculations(self.slab, params)
        assert len(traces) == 6
        assert all(t.success for t in traces)
        wl = self.slab.weak_layer
        assert wl is not None
        assert wl.G_c is not None
        assert wl.G_Ic is not None
        assert wl.G_IIc is not None
        assert wl.sigma_c is not None
        assert wl.tau_c is not None
        assert wl.sigma_comp is not None

    def test_trace_output_is_ufloat(self):
        """ComputationTrace.output for weak-layer params should be a UFloat."""
        import uncertainties
        params = {"G_Ic": "weissgraeber_rosendahl"}
        traces = self.executor._execute_weak_layer_calculations(self.slab, params)
        assert isinstance(traces[0].output, uncertainties.UFloat)

    def test_trace_parameter_name_matches(self):
        params = {"tau_c": "weissgraeber_rosendahl"}
        traces = self.executor._execute_weak_layer_calculations(self.slab, params)
        assert traces[0].parameter == "tau_c"

    def test_trace_layer_index_is_none(self):
        """Weak-layer params are slab-level; layer_index should be None."""
        params = {"G_c": "weissgraeber_rosendahl"}
        traces = self.executor._execute_weak_layer_calculations(self.slab, params)
        assert traces[0].layer_index is None


# ---------------------------------------------------------------------------
# Integration — full pipeline to g_delta (requires weac)
# ---------------------------------------------------------------------------

class TestFullPipelineStability:
    """End-to-end tests: graph-based pathway execution targeting g_delta."""

    @requires_weac
    def test_find_parameterizations_for_g_delta(self):
        """find_parameterizations should find at least one pathway to g_delta."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.graph.parameter_graph import graph

        g_delta_node = graph.get_node("g_delta")
        assert g_delta_node is not None
        pathways = find_parameterizations(graph, g_delta_node)
        assert len(pathways) > 0

    @requires_weac
    def test_execute_pathway_to_g_delta_succeeds(self):
        """Executing a g_delta pathway should produce a successful PathwayResult."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.execution.config import ExecutionConfig
        from snowpyt_mechparams.execution.executor import PathwayExecutor
        from snowpyt_mechparams.graph.parameter_graph import graph
        from snowpyt_mechparams.stability_criteria.weac.weac_result import WeacSkierResult

        slab = _make_slab_for_stability()
        g_delta_node = graph.get_node("g_delta")
        pathways = find_parameterizations(graph, g_delta_node)
        assert pathways, "No pathways found for g_delta"

        executor = PathwayExecutor()
        config = ExecutionConfig()

        # Use any valid pathway
        result = executor.execute_parameterization(
            pathways[0], slab, "g_delta", config
        )
        assert result.success, f"Pathway failed: {result.computation_trace}"
        assert result.slab.weac_result is not None
        assert isinstance(result.slab.weac_result, WeacSkierResult)

    @requires_weac
    def test_g_delta_in_trace(self):
        """The computation trace should include a successful g_delta entry."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.execution.config import ExecutionConfig
        from snowpyt_mechparams.execution.executor import PathwayExecutor
        from snowpyt_mechparams.graph.parameter_graph import graph

        slab = _make_slab_for_stability()
        g_delta_node = graph.get_node("g_delta")
        pathways = find_parameterizations(graph, g_delta_node)

        executor = PathwayExecutor()
        config = ExecutionConfig()
        result = executor.execute_parameterization(
            pathways[0], slab, "g_delta", config
        )

        g_delta_traces = [t for t in result.computation_trace if t.parameter == "g_delta"]
        assert len(g_delta_traces) == 1
        assert g_delta_traces[0].success
        assert isinstance(g_delta_traces[0].output, float)

    @requires_weac
    def test_weak_layer_populated_after_execution(self):
        """After execution, result_slab.weak_layer should have all six fracture params."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.execution.config import ExecutionConfig
        from snowpyt_mechparams.execution.executor import PathwayExecutor
        from snowpyt_mechparams.graph.parameter_graph import graph

        slab = _make_slab_for_stability()
        g_delta_node = graph.get_node("g_delta")
        pathways = find_parameterizations(graph, g_delta_node)

        executor = PathwayExecutor()
        config = ExecutionConfig()
        result = executor.execute_parameterization(
            pathways[0], slab, "g_delta", config
        )

        wl = result.slab.weak_layer
        assert wl is not None
        assert wl.G_c is not None
        assert wl.G_Ic is not None
        assert wl.G_IIc is not None
        assert wl.sigma_c is not None
        assert wl.tau_c is not None
        assert wl.sigma_comp is not None
