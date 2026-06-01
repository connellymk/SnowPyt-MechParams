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
