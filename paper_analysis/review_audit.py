"""Read-only cohort audits and an analysis-only density assignment policy."""

from __future__ import annotations

import hashlib
import math
from collections import Counter

from uncertainties import ufloat

from review_metrics import number


def scalar(value, kind="length"):
    """Normalize raw CAAML lengths to cm and densities to kg/m³; no tolerance."""
    try:
        if isinstance(value, (list, tuple)):
            x, unit = float(value[0]), str(value[1]).lower().replace("³", "3").replace(
                "^", ""
            )
        else:
            return float(value)
        factors = (
            {"cm": 1.0, "m": 100.0, "mm": 0.1}
            if kind == "length"
            else {
                "kgm-3": 1.0,
                "kg/m3": 1.0,
                "kg m-3": 1.0,
                "g/cm3": 1000.0,
                "gcm-3": 1000.0,
            }
        )
        return x * factors[unit]
    except (ValueError, TypeError, IndexError, KeyError):
        return math.nan


def interval(obj):
    top, thickness = scalar(getattr(obj, "depth_top", None)), scalar(
        getattr(obj, "thickness", None)
    )
    return (
        (top, top + thickness)
        if math.isfinite(top) and thickness > 0 and math.isfinite(thickness)
        else None
    )


def density_audit(raw):
    """Return observation- and layer-level ledgers without modifying a profile.

    Geometric categories overlap intentionally. Candidate assignment requires a
    valid sample fully contained by exactly one valid layer. Multiple contained
    observations (including invalid/ambiguous ones) prevent the fallback.
    """
    layers = raw.snow_profile.layers or []
    samples = raw.snow_profile.density_profile or []
    bounds = [interval(layer) for layer in layers]
    observations = []
    for j, sample in enumerate(samples):
        sb = interval(sample)
        point_depth = scalar(getattr(sample, "depth_top", None))
        rho = scalar(getattr(sample, "density", None), "density")
        containers = [
            i
            for i, b in enumerate(bounds)
            if b and sb and b[0] <= sb[0] and sb[1] <= b[1]
        ]
        exact = [i for i, b in enumerate(bounds) if b and sb and b == sb]
        overlaps = [
            i
            for i, b in enumerate(bounds)
            if b and sb and max(b[0], sb[0]) < min(b[1], sb[1])
        ]
        point_layers = [
            i
            for i, b in enumerate(bounds)
            if b and sb is None and b[0] <= point_depth < b[1]
        ]
        observations.append(
            {
                "sample_index": j,
                "density": rho,
                "bounds": sb,
                "containers": containers,
                "exact_layers": exact,
                "overlap_layers": overlaps,
                "point_layers": point_layers,
                "invalid_interval": sb is None,
                "invalid_density": not math.isfinite(rho) or rho <= 0,
                "valid": bool(sb and math.isfinite(rho) and rho > 0),
                "boundary_crossing": bool(overlaps and not containers),
                "ambiguous": len(containers) > 1,
            }
        )
    ledger = []
    for i, layer in enumerate(layers):
        exact_raw = [
            j
            for j, s in enumerate(samples)
            if s.depth_top == layer.depth_top and s.thickness == layer.thickness
        ]
        exact = [o for o in observations if i in o["exact_layers"]]
        contained = [o for o in observations if i in o["containers"]]
        overlaps = [o for o in observations if i in o["overlap_layers"]]
        point_samples = [o for o in observations if i in o["point_layers"]]
        selected, policy = None, "unmatched"
        if exact_raw:
            policy = "original_exact"  # Preserve current first match, even if invalid.
        elif exact:
            first = exact[0]
            if first["valid"] and len(first["containers"]) == 1:
                selected, policy = first, "normalized_exact"
        elif (
            len(contained) == 1
            and contained[0]["valid"]
            and len(contained[0]["containers"]) == 1
        ):
            selected, policy = contained[0], "single_contained"
        fraction = None
        if selected:
            fraction = (selected["bounds"][1] - selected["bounds"][0]) / (
                bounds[i][1] - bounds[i][0]
            )
        ledger.append(
            {
                "layer_index": i,
                "raw_exact_count": len(exact_raw),
                "normalized_exact_count": len(exact),
                "contained_count": len(contained),
                "overlap_count": len(overlaps),
                "policy": policy,
                "point_sample_count": len(point_samples),
                "sample_index": selected["sample_index"] if selected else None,
                "density": selected["density"] if selected else None,
                "sampled_fraction": fraction,
                "processing_excluded": bool(
                    not exact_raw and (overlaps or point_samples)
                ),
            }
        )
    return observations, ledger


def assign_contained(raw, pit):
    """Modify only this analysis Pit, never raw CAAML or the production parser."""
    _, ledger = density_audit(raw)
    for row, layer in zip(ledger, pit.layers, strict=True):
        if layer.density_measured is None and row["density"] is not None:
            layer.density_measured = ufloat(row["density"], 0.1 * abs(row["density"]))
    return ledger


def audit_profile(raw, pit, filename, sha256):
    observations, layers = density_audit(raw)
    angle = number(pit.slope_angle)
    issues = Counter()
    if math.isfinite(angle) and not 0 <= angle <= 90:
        issues["slope_outside_0_90"] += 1
    previous_bottom = None
    for layer in pit.layers:
        top, thickness = number(layer.depth_top), number(layer.thickness)
        if not math.isfinite(top) or top < 0:
            issues["invalid_layer_top"] += 1
        if not math.isfinite(thickness) or thickness <= 0:
            issues["invalid_layer_thickness"] += 1
        if previous_bottom is not None and math.isfinite(top):
            if top > previous_bottom:
                issues["layer_gap"] += 1
            elif top < previous_bottom:
                issues["layer_overlap"] += 1
        previous_bottom = top + thickness
        rho = number(layer.density_measured)
        if math.isfinite(rho) and (rho <= 0 or rho > 917):
            issues["measured_density_outside_0_917"] += 1
        gs = number(layer.grain_size_avg)
        if math.isfinite(gs) and gs <= 0:
            issues["nonpositive_grain_size"] += 1
        if layer.hand_hardness and layer.hand_hardness_index is None:
            issues["unknown_hand_hardness"] += 1
    tests = pit._get_matching_ect_results()
    exclusions = Counter()
    for test in tests:
        depth = getattr(test, "depth_top", None)
        depth = number(
            depth[0] if isinstance(depth, (tuple, list)) and depth else depth
        )
        containers = [
            layer
            for layer in pit.layers
            if number(layer.depth_top) <= depth < number(layer.depth_bottom)
        ]
        if not math.isfinite(depth):
            exclusions["missing_failure_depth"] += 1
        elif not containers:
            exclusions["failure_depth_outside_layers"] += 1
        elif not any(
            number(layer.depth_top) < number(containers[0].depth_top)
            for layer in pit.layers
        ):
            exclusions["no_overlying_layer"] += 1
        if len(containers) > 1:
            issues["ambiguous_failure_layer_first_retained"] += 1
    slabs = pit.create_slabs("ECTP_failure_layer")
    assert len(tests) == len(slabs) + sum(exclusions.values())
    fingerprints = []
    for slab in slabs:
        signature = [
            (
                number(layer.depth_top),
                number(layer.thickness),
                layer.grain_form,
                layer.hand_hardness,
                number(layer.density_measured),
                number(layer.grain_size_avg),
            )
            for layer in slab.layers
        ]
        fingerprints.append(hashlib.sha256(repr(signature).encode()).hexdigest())
    return (
        {
            "filename": filename,
            "sha256": sha256,
            "pit_id": pit.pit_id,
            "layers": len(pit.layers),
            "density_observations": len(observations),
            "qualifying_tests": len(tests),
            "slabs": len(slabs),
            "issues": dict(issues),
            "exclusions": dict(exclusions),
            "repeated_stratigraphies_within_pit": len(fingerprints)
            - len(set(fingerprints)),
        },
        observations,
        layers,
    )
