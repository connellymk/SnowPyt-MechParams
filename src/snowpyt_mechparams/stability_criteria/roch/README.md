# stability_criteria.roch

Roch/Fohn stability-index calculations.

The module computes gravitational shear stress from slab density, layer thickness, and slope angle, then compares that stress with a caller-supplied weak-layer shear strength. It can also include an externally supplied skier stress term.

Inputs should already carry uncertainty where desired; the calculations preserve `uncertainties` arithmetic.
