# methods.slab

Formula implementations for whole-slab targets.

Current targets:

- `A11`, `B11`, `D11`, and `A55` from the Weissgraeber/Rosendahl laminate-theory formulation.
- `slab_weight`, `slab_weight_shear`, and `slab_weight_shear_with_elasticity` coverage helpers in `coverage.py`.

Slab methods receive a `Slab` with pathway-specific layer values already materialized by the execution context. They should not mutate source slabs directly.
