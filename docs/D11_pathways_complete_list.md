# Complete List of 32 Pathways to Calculate D11

This document lists all 32 unique calculation pathways discovered by the parameterization algorithm to calculate D11 (bending stiffness) from snow pit measurements.

## Summary

**Total Pathways**: 32

**Calculation Structure**:
- Each pathway calculates D11 using the Weißgraeber & Rosendahl (2023) classical laminate theory method
- D11 requires: layer positions (zi), elastic modulus (E), and Poisson's ratio (ν) for all layers
- The pathways differ in how they calculate the required density (ρ), E, and ν values

## Method Combinations

### Density Methods (4 options)
1. **direct** - Direct measurement from snow pit data
2. **geldsetzer** - Geldsetzer et al. (2009) from hand hardness and grain form
3. **kim_jamieson_table2** - Kim & Jamieson (2010) Table 2 from hand hardness and grain form
4. **kim_jamieson_table5** - Kim & Jamieson (2010) Table 5 from hand hardness, grain form, and grain size

### Elastic Modulus Methods (4 options)
1. **bergfeld** - Bergfeld et al. (2023) from density and grain form
2. **kochle** - Köchle & Schneebeli (2014) from density and grain form
3. **wautier** - Wautier et al. (2015) from density and grain form
4. **schottner** - Schöttner et al. (2024) from density and grain form

### Poisson's Ratio Methods (2 options)
1. **kochle** - Köchle & Schneebeli (2014) from grain form only (no density required)
2. **srivastava** - Srivastava et al. (2016) from hand hardness and grain form (NOT from density)

### Slab Parameter Method (1 option)
1. **weissgraeber_rosendahl** - Weißgraeber & Rosendahl (2023) classical laminate theory

## Important Note About Poisson's Ratio

**Key correction**: The Srivastava method for Poisson's ratio uses **hand hardness + grain form** directly, NOT calculated density. This is different from elastic modulus methods, which require density to be calculated first.

Graph structure:
```
measured_hand_hardness + measured_grain_form → merge_hh_gf → srivastava → poissons_ratio
measured_grain_form → kochle → poissons_ratio
```

## All 32 Pathways

```
 1. ρ: direct               | E: bergfeld   | ν: kochle       | D11: weissgraeber_rosendahl
 2. ρ: direct               | E: bergfeld   | ν: srivastava   | D11: weissgraeber_rosendahl
 3. ρ: geldsetzer           | E: bergfeld   | ν: kochle       | D11: weissgraeber_rosendahl
 4. ρ: geldsetzer           | E: bergfeld   | ν: srivastava   | D11: weissgraeber_rosendahl
 5. ρ: kim_jamieson_table2  | E: bergfeld   | ν: kochle       | D11: weissgraeber_rosendahl
 6. ρ: kim_jamieson_table2  | E: bergfeld   | ν: srivastava   | D11: weissgraeber_rosendahl
 7. ρ: kim_jamieson_table5  | E: bergfeld   | ν: kochle       | D11: weissgraeber_rosendahl
 8. ρ: kim_jamieson_table5  | E: bergfeld   | ν: srivastava   | D11: weissgraeber_rosendahl
 9. ρ: direct               | E: kochle     | ν: kochle       | D11: weissgraeber_rosendahl
10. ρ: direct               | E: kochle     | ν: srivastava   | D11: weissgraeber_rosendahl
11. ρ: geldsetzer           | E: kochle     | ν: kochle       | D11: weissgraeber_rosendahl
12. ρ: geldsetzer           | E: kochle     | ν: srivastava   | D11: weissgraeber_rosendahl
13. ρ: kim_jamieson_table2  | E: kochle     | ν: kochle       | D11: weissgraeber_rosendahl
14. ρ: kim_jamieson_table2  | E: kochle     | ν: srivastava   | D11: weissgraeber_rosendahl
15. ρ: kim_jamieson_table5  | E: kochle     | ν: kochle       | D11: weissgraeber_rosendahl
16. ρ: kim_jamieson_table5  | E: kochle     | ν: srivastava   | D11: weissgraeber_rosendahl
17. ρ: direct               | E: wautier    | ν: kochle       | D11: weissgraeber_rosendahl
18. ρ: direct               | E: wautier    | ν: srivastava   | D11: weissgraeber_rosendahl
19. ρ: geldsetzer           | E: wautier    | ν: kochle       | D11: weissgraeber_rosendahl
20. ρ: geldsetzer           | E: wautier    | ν: srivastava   | D11: weissgraeber_rosendahl
21. ρ: kim_jamieson_table2  | E: wautier    | ν: kochle       | D11: weissgraeber_rosendahl
22. ρ: kim_jamieson_table2  | E: wautier    | ν: srivastava   | D11: weissgraeber_rosendahl
23. ρ: kim_jamieson_table5  | E: wautier    | ν: kochle       | D11: weissgraeber_rosendahl
24. ρ: kim_jamieson_table5  | E: wautier    | ν: srivastava   | D11: weissgraeber_rosendahl
25. ρ: direct               | E: schottner  | ν: kochle       | D11: weissgraeber_rosendahl
26. ρ: direct               | E: schottner  | ν: srivastava   | D11: weissgraeber_rosendahl
27. ρ: geldsetzer           | E: schottner  | ν: kochle       | D11: weissgraeber_rosendahl
28. ρ: geldsetzer           | E: schottner  | ν: srivastava   | D11: weissgraeber_rosendahl
29. ρ: kim_jamieson_table2  | E: schottner  | ν: kochle       | D11: weissgraeber_rosendahl
30. ρ: kim_jamieson_table2  | E: schottner  | ν: srivastava   | D11: weissgraeber_rosendahl
31. ρ: kim_jamieson_table5  | E: schottner  | ν: kochle       | D11: weissgraeber_rosendahl
32. ρ: kim_jamieson_table5  | E: schottner  | ν: srivastava   | D11: weissgraeber_rosendahl
```

## Pathway Groupings

### By Elastic Modulus Method

**Bergfeld (8 pathways)**: #1-8
- 4 density methods × 2 Poisson's ratio methods

**Köchle (8 pathways)**: #9-16
- 4 density methods × 2 Poisson's ratio methods

**Wautier (8 pathways)**: #17-24
- 4 density methods × 2 Poisson's ratio methods

**Schöttner (8 pathways)**: #25-32
- 4 density methods × 2 Poisson's ratio methods

### By Poisson's Ratio Method

**Köchle (16 pathways)**: #1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31
- Uses grain form only (no density calculation needed)
- 4 density methods for E × 4 E methods = 16 pathways

**Srivastava (16 pathways)**: #2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32
- Uses hand hardness + grain form (independent of density calculation for E)
- 4 density methods for E × 4 E methods = 16 pathways

## Complete Method Combination Matrix

| Density Method     | E Method  | ν Method    | Pathway # |
|--------------------|-----------|-------------|-----------|
| direct             | bergfeld  | kochle      | 1         |
| direct             | bergfeld  | srivastava  | 2         |
| geldsetzer         | bergfeld  | kochle      | 3         |
| geldsetzer         | bergfeld  | srivastava  | 4         |
| kim_jamieson_table2| bergfeld  | kochle      | 5         |
| kim_jamieson_table2| bergfeld  | srivastava  | 6         |
| kim_jamieson_table5| bergfeld  | kochle      | 7         |
| kim_jamieson_table5| bergfeld  | srivastava  | 8         |
| direct             | kochle    | kochle      | 9         |
| direct             | kochle    | srivastava  | 10        |
| geldsetzer         | kochle    | kochle      | 11        |
| geldsetzer         | kochle    | srivastava  | 12        |
| kim_jamieson_table2| kochle    | kochle      | 13        |
| kim_jamieson_table2| kochle    | srivastava  | 14        |
| kim_jamieson_table5| kochle    | kochle      | 15        |
| kim_jamieson_table5| kochle    | srivastava  | 16        |
| direct             | wautier   | kochle      | 17        |
| direct             | wautier   | srivastava  | 18        |
| geldsetzer         | wautier   | kochle      | 19        |
| geldsetzer         | wautier   | srivastava  | 20        |
| kim_jamieson_table2| wautier   | kochle      | 21        |
| kim_jamieson_table2| wautier   | srivastava  | 22        |
| kim_jamieson_table5| wautier   | kochle      | 23        |
| kim_jamieson_table5| wautier   | srivastava  | 24        |
| direct             | schottner | kochle      | 25        |
| direct             | schottner | srivastava  | 26        |
| geldsetzer         | schottner | kochle      | 27        |
| geldsetzer         | schottner | srivastava  | 28        |
| kim_jamieson_table2| schottner | kochle      | 29        |
| kim_jamieson_table2| schottner | srivastava  | 30        |
| kim_jamieson_table5| schottner | kochle      | 31        |
| kim_jamieson_table5| schottner | srivastava  | 32        |

## Why Exactly 32 Pathways?

The calculation is straightforward:

**4 density methods** × **4 elastic modulus methods** × **2 Poisson's ratio methods** = **32 pathways**

Key insights:
1. **Density** is calculated once per layer and used by E methods
2. **Poisson's ratio (Srivastava)** does NOT depend on the calculated density value - it uses the same measured inputs (hand hardness + grain form) that the density estimation methods use
3. **Poisson's ratio (Köchle)** uses only grain form, independent of all density calculations
4. Each combination of (density method, E method, ν method) represents a unique calculation pathway

## Graph Structure Summary

```
Layer-level calculations:
  snow_pit → measured_density → density (direct)
  snow_pit → measured_hand_hardness + measured_grain_form → merge_hh_gf → density (geldsetzer, kim_table2)
  snow_pit → merge_hh_gf + measured_grain_size → merge_hh_gf_gs → density (kim_table5)

  density + grain_form → merge_density_grain_form → elastic_modulus (4 methods)

  grain_form → poissons_ratio (kochle)
  merge_hh_gf → poissons_ratio (srivastava)

Slab-level calculations:
  layer_thickness → zi (spatial information)
  elastic_modulus + poissons_ratio → merge_E_nu
  zi + merge_E_nu → merge_zi_E_nu → D11 (weissgraeber_rosendahl)
```

## Notes

- All pathways calculate D11 using the same final method (Weißgraeber & Rosendahl 2023)
- Pathways differ in the intermediate steps to calculate required inputs (ρ, E, ν)
- Some pathways may fail for specific snow pits if required measurements are missing
- The execution engine uses dynamic programming to cache intermediate results, so computing all 32 pathways is efficient
- Expected success rates vary by pathway based on data availability in the SnowPilot dataset

## References

See the main README.md for full citations of all methods.

---

**Generated**: February 2026
**Algorithm**: `snowpyt_mechparams.algorithm.find_parameterizations()`
**Graph Version**: v0.3.0 (corrected)
