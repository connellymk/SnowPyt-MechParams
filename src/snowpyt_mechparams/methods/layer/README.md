# methods.layer

Formula implementations for per-layer mechanical parameters.

Current targets:

- `density`: direct measured density plus Geldsetzer and Kim/Jamieson estimates.
- `elastic_modulus`: Bergfeld, Kochle, Wautier, and Schottner estimates.
- `poissons_ratio`: Kochle and Srivastava estimates.
- `shear_modulus`: Lame relationship from elastic modulus and Poisson's ratio.

These modules expose calculation functions only. Dependency metadata, output attributes, and graph wiring belong in `methods.registry`.
