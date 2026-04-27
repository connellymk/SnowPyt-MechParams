# stability_criteria

Direct stability-criterion APIs.

This package currently contains Roch-style limit-equilibrium calculations and a WEAC skier-load adapter. These criteria are not graph targets because they require weak-layer strength or fracture inputs that are not generally derivable from standard snow pit observations.

Use this package after layer and slab parameters have been computed by `execution`, or when callers provide the required mechanical inputs directly.
