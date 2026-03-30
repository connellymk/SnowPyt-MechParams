# WeakLayer data structure — a snow weak layer with fracture/strength parameters

import dataclasses
from dataclasses import dataclass
from typing import Optional

from snowpyt_mechparams.models._types import UncertainValue
from snowpyt_mechparams.models.layer import Layer


@dataclass
class WeakLayer(Layer):
    """
    A snow weak layer: all measured ``Layer`` fields plus the six computed
    fracture and strength parameters required by WEAC's coupled criterion.

    Inherits all ``Layer`` fields (thickness, density_measured, hand_hardness,
    grain_form, grain_size_avg, depth_top, layer_of_concern, and the computed
    density_calculated, elastic_modulus, poissons_ratio, shear_modulus).

    The six fracture/strength fields default to ``None``.  The WEAC adapter
    (``calculate_weac_skier``) falls back to WEAC's built-in defaults for any
    field that is ``None``.

    Notes
    -----
    Values can be plain ``float`` or ``uncertainties.UFloat``.  Because WEAC
    uses ``scipy.linalg.eig`` internally, ``UFloat`` values are stripped to
    their nominal values at the adapter boundary — uncertainties are **not**
    propagated through WEAC results.

    Attributes
    ----------
    G_c : Optional[UncertainValue]
        Total fracture energy [J/m²].  WEAC default: 1.0 J/m².
    G_Ic : Optional[UncertainValue]
        Mode-I fracture toughness [J/m²].  WEAC default: 0.56 J/m².
    G_IIc : Optional[UncertainValue]
        Mode-II fracture toughness [J/m²].  WEAC default: 0.79 J/m².
    sigma_c : Optional[UncertainValue]
        Tensile normal strength [kPa].  WEAC default: 6.16 kPa.
    tau_c : Optional[UncertainValue]
        Shear strength [kPa].  WEAC default: 5.09 kPa.
    sigma_comp : Optional[UncertainValue]
        Compressive strength [kPa].  WEAC default: 2.6 kPa.
    """

    G_c: Optional[UncertainValue] = None        # J/m²  — total fracture energy (WEAC default 1.0)
    G_Ic: Optional[UncertainValue] = None       # J/m²  — mode-I fracture toughness (WEAC default 0.56)
    G_IIc: Optional[UncertainValue] = None      # J/m²  — mode-II fracture toughness (WEAC default 0.79)
    sigma_c: Optional[UncertainValue] = None    # kPa   — tensile normal strength (WEAC default 6.16)
    tau_c: Optional[UncertainValue] = None      # kPa   — shear strength (WEAC default 5.09)
    sigma_comp: Optional[UncertainValue] = None # kPa   — compressive strength (WEAC default 2.6)

    @classmethod
    def from_layer(cls, layer: "Layer") -> "WeakLayer":
        """Create a WeakLayer from a plain Layer, copying all Layer fields.

        The six fracture/strength parameters (G_c, G_Ic, G_IIc, sigma_c,
        tau_c, sigma_comp) are left as None and populated later by the
        execution engine.
        """
        return cls(**{f.name: getattr(layer, f.name) for f in dataclasses.fields(layer)})
