# WeakLayer data structure — a snow weak layer beneath the slab

import dataclasses
from dataclasses import dataclass

from snowpyt_mechparams.models.layer import Layer


@dataclass
class WeakLayer(Layer):
    """
    A snow weak layer: all measured ``Layer`` fields, used to identify the
    layer beneath the slab.

    Inherits all ``Layer`` fields (thickness, density_measured, hand_hardness,
    grain_form, grain_size_avg, depth_top, layer_of_concern, and the computed
    density_calculated, elastic_modulus, poissons_ratio, shear_modulus).

    Fracture and strength parameters (G_c, G_Ic, G_IIc, sigma_c, tau_c,
    sigma_comp) are not stored here — they are currently represented in the
    graph by the ``weak_layer_info*`` placeholder node.
    """

    @classmethod
    def from_layer(cls, layer: "Layer") -> "WeakLayer":
        """Create a WeakLayer from a plain Layer, copying all Layer fields."""
        return cls(**{f.name: getattr(layer, f.name) for f in dataclasses.fields(layer)})
