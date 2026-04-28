"""Fast smoke tests for documented research workflows."""

from pathlib import Path

from uncertainties import ufloat

from snowpyt_mechparams import ExecutionEngine
from snowpyt_mechparams.execution import ExecutionConfig
from snowpyt_mechparams.models import Layer, Pit, Slab
from snowpyt_mechparams.snowpilot import parse_caaml_file


def test_documented_quick_start_runs():
    """The synthetic quick-start slab should execute at least one D11 pathway."""
    layers = [
        Layer(depth_top=ufloat(0, 0.2), thickness=ufloat(20, 1), hand_hardness="1F", grain_form="RG"),
        Layer(
            depth_top=ufloat(20, 0.2),
            thickness=ufloat(25, 1),
            density_measured=ufloat(220, 20),
            grain_form="DF",
        ),
    ]
    slab = Slab(layers=layers, angle=35.0)

    results = ExecutionEngine().execute_all(
        slab,
        target_parameter="D11",
        config=ExecutionConfig(include_method_uncertainty=False),
    )

    assert results.total_pathways == 32
    assert results.successful_pathways > 0


def test_packaged_sample_data_produces_ectp_slab_and_shear_weight():
    """The packaged CAAML sample should parse and support a small execution run."""
    repo_root = Path(__file__).resolve().parents[1]
    sample = repo_root / "examples" / "sample_data" / "snowpits-27829-caaml.xml"

    pit = Pit.from_snow_pit(parse_caaml_file(str(sample)))
    slabs = pit.create_slabs("ECTP_failure_layer")

    assert len(slabs) == 1
    assert len(slabs[0].layers) == 2

    results = ExecutionEngine().execute_all(
        slabs[0],
        "slab_weight_shear",
        config=ExecutionConfig(include_method_uncertainty=False),
    )

    assert results.total_pathways == 4
    assert results.successful_pathways > 0
