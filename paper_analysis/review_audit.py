"""Read-only density/cohort audits; no replacement density assignment policy."""

from __future__ import annotations

import hashlib
import math
from collections import Counter

from review_metrics import number


def scalar(value, kind="length"):
    """Normalize raw CAAML lengths to cm and densities to kg/m³ for auditing."""
    try:
        if not isinstance(value, (list, tuple)):
            return float(value)
        x, unit = float(value[0]), str(value[1]).lower().replace("³", "3").replace(
            "^", ""
        )
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
    top = scalar(getattr(obj, "depth_top", None))
    thickness = scalar(getattr(obj, "thickness", None))
    return (
        (top, top + thickness)
        if math.isfinite(top) and math.isfinite(thickness) and thickness > 0
        else None
    )


def density_audit(raw):
    """Inspect exact, contained, crossing, and point samples without assigning them.

    Raw equality mirrors production matching, including first-match behavior.
    Normalized geometry is only descriptive; overlapping categories are not summed.
    """
    layers = raw.snow_profile.layers or []
    samples = raw.snow_profile.density_profile or []
    bounds = [interval(layer) for layer in layers]
    observations = []
    for j, sample in enumerate(samples):
        sb = interval(sample)
        depth = scalar(getattr(sample, "depth_top", None))
        rho = scalar(getattr(sample, "density", None), "density")
        exact = [
            i
            for i, layer in enumerate(layers)
            if sample.depth_top == layer.depth_top
            and sample.thickness == layer.thickness
        ]
        containers = [
            i
            for i, b in enumerate(bounds)
            if b and sb and b[0] <= sb[0] and sb[1] <= b[1]
        ]
        overlaps = [
            i
            for i, b in enumerate(bounds)
            if b and sb and max(b[0], sb[0]) < min(b[1], sb[1])
        ]
        points = [
            i for i, b in enumerate(bounds) if b and sb is None and b[0] <= depth < b[1]
        ]
        observations.append(
            dict(
                sample_index=j,
                exact_layers=exact,
                containers=containers,
                overlap_layers=overlaps,
                point_layers=points,
                invalid_interval=sb is None,
                invalid_density=not math.isfinite(rho) or rho <= 0,
                boundary_crossing=bool(overlaps and not containers),
                ambiguous=len(containers) > 1,
            )
        )
    ledger = []
    for i in range(len(layers)):
        exact = [o for o in observations if i in o["exact_layers"]]
        excluded = [
            o
            for o in observations
            if i in o["overlap_layers"] or i in o["point_layers"]
        ]
        ledger.append(
            dict(
                layer_index=i,
                raw_exact_count=len(exact),
                processing_excluded=bool(not exact and excluded),
            )
        )
    return observations, ledger


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


def load_audited_pits(data_dir):
    """Load the unchanged production cohort and mark diagnostic provenance only."""
    from pathlib import Path
    from snowpyt_mechparams.models import Pit
    from snowpyt_mechparams.snowpilot import parse_caaml_file

    paths = sorted(Path(data_dir).glob("*.xml"))
    pits, profiles, observations, hashes, manifest_rows = [], [], [], [], []
    issues, exclusions = Counter(), Counter()
    layers_total = processing_layers = 0
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = parse_caaml_file(str(path))
        pit = Pit.from_snow_pit(raw)
        profile, obs, ledger = audit_profile(raw, pit, path.name, digest)
        for layer, entry in zip(pit.layers, ledger):
            layer._review_density_processing_excluded = entry["processing_excluded"]
        pits.append(pit)
        profiles.append(profile)
        observations.extend(obs)
        hashes.append(digest)
        manifest_rows.append(f"{path.name}\t{digest}\n")
        issues.update(profile["issues"])
        exclusions.update(profile["exclusions"])
        layers_total += len(pit.layers)
        processing_layers += sum(x["processing_excluded"] for x in ledger)
    slabs = [s for p in pits for s in p.create_slabs("ECTP_failure_layer")]
    counts = Counter(s.pit_id for s in slabs)
    summary = dict(
        files=len(paths),
        parsed_pits=len(pits),
        layers=layers_total,
        slabs=len(slabs),
        contributing_pits=len(counts),
        pits_with_multiple_slabs=sum(n > 1 for n in counts.values()),
        duplicate_file_content_excess=sum(n - 1 for n in Counter(hashes).values()),
        duplicate_pit_id_excess=sum(
            n - 1 for n in Counter(p.pit_id for p in pits).values()
        ),
        repeated_stratigraphies_within_pit=sum(
            p["repeated_stratigraphies_within_pit"] for p in profiles
        ),
        issues=dict(issues),
        slab_exclusions=dict(exclusions),
        density_observations=len(observations),
        density_observations_exact=sum(bool(o["exact_layers"]) for o in observations),
        unmatched_with_usable_contained_interval=sum(
            bool(not o["exact_layers"] and o["containers"] and not o["invalid_density"])
            for o in observations
        ),
        observations_with_unusable_interval=sum(
            o["invalid_interval"] for o in observations
        ),
        point_observations_located_in_layer=sum(
            bool(o["point_layers"]) for o in observations
        ),
        invalid_density_values=sum(o["invalid_density"] for o in observations),
        processing_excluded_layers=processing_layers,
        input_manifest_sha256=hashlib.sha256(
            "".join(manifest_rows).encode()
        ).hexdigest(),
    )
    return pits, summary
