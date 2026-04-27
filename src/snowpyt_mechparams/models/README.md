# models

Domain objects for snow pit observations and computed mechanical parameters.

- `Layer` represents one snow layer and stores measured density, hand hardness, grain form, grain size, thickness, and computed layer properties.
- `WeakLayer` extends `Layer` for the weak layer beneath a slab.
- `Slab` groups the layers above a weak layer and stores slope angle, metadata, slab stiffnesses, slab-weight outputs, and stability results.
- `Pit` converts parsed SnowPilot data into slabs for downstream analysis.

Model classes should stay calculation-light. New empirical or mechanical formulas belong in `methods`, and execution should write results back through the output attributes declared in `MethodSpec`.
