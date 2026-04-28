# stability_criteria.weac

Adapter for the WEAC skier-load fracture-mechanics criterion.

The adapter translates SnowPyt `Slab` data into the optional `weac` package input format, applies weak-layer defaults or caller overrides, and returns a `WeacSkierResult`.

The external WEAC solver uses plain floats, so uncertain inputs are converted to nominal values at the adapter boundary.
