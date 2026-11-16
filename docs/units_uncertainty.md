# Units And Uncertainty

SnowPyt-MechParams accepts plain numbers or `uncertainties.ufloat` values for
measured inputs. When inputs carry uncertainty, the package preserves
`uncertainties` arithmetic through layer and slab calculations whenever the
underlying formula supports it.

## Input Units

Use these units when constructing model objects directly:

| Field | Unit | Notes |
| --- | --- | --- |
| `Layer.depth_top` | cm | Depth below snow surface. |
| `Layer.thickness` | cm | Converted to mm inside slab stiffness formulas. |
| `Layer.density_measured` | kg/m^3 | Direct measured density. |
| `Layer.grain_size_avg` | mm | Used by Kim and Jamieson Equation 5 / Table 6 density. |
| `Slab.angle` | degrees | Slope angle, used by slab-weight shear projections. |

Layer elastic and shear moduli are reported in MPa. Slab stiffness outputs use
the units documented on `Slab`: `A11` and `A55` in N/mm, `B11` in N, and `D11`
in N*mm. Slab weight outputs are per-unit-area loads in N/m^2.

## Measurement Uncertainty

SnowPilot/CAAML parsing applies the package's standard field-measurement
uncertainties where those values are available. Directly constructed objects can
use `ufloat` values to make measurement uncertainty explicit.

The parser assigns density 10%, thickness 5%, slope 2°, hand-hardness index 0.67,
and grain size 48% of magnitude as symmetric standard deviations. The grain-size
choice approximates the lower side of proposed asymmetric −48%/+122% percentile
bounds; a single `ufloat` cannot represent them. It is an assigned modeling
uncertainty, not the original interval or an established observation-error
distribution. Legacy `U_GRAIN_SIZE = 0.5` mm remains available but is no longer
used in parsing.

Applicability and the Köchle branch use nominal density; uncertainties crossing
limits are not clipped. Primary analyses treat distinct layer observations as
independent. Density methods reconstruct ufloats, so callers must not assume
arbitrary input covariance survives those interfaces.

D11 uses upward-positive z. Reference depth is the first layer top plus half the
sum of thicknesses, not generally the neutral axis. Measured tops remain fixed
while thicknesses carry uncertainty. Gaps are retained; the reference is therefore
not the midpoint of the bounding interval in gapped profiles. Divide N·mm by 1000
for N·m. No observation-orientation conversion is inferred from unavailable data.

## Method Uncertainty

`ExecutionConfig(include_method_uncertainty=True)` is the default. When enabled,
empirical methods add their published regression or fit uncertainty where the
implementation has that information. Set it to `False` when you want only input
measurement uncertainty to propagate:

```python
from snowpyt_mechparams.execution import ExecutionConfig

config = ExecutionConfig(include_method_uncertainty=False)
```

Some mechanics-based relationships accept the flag for API consistency but do
not add a separate empirical method uncertainty.
