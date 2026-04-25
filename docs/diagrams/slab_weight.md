# SnowPyt-MechParams — Slab Weight Pathways

```mermaid
graph LR

    measured_slope_angle[slope angle]
    measured_layer_thickness[layer thickness]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    slab_weight[slab weight (W)]
    slab_weight_shear[slab weight_shear (W_s)]
    slab_weight_shear_with_elasticity[slab weight_shear with elasticity]
    merge_slab_weight_inputs{ρ + h_i}
    merge_slab_weight_slope_angle{W + slope angle}
    merge_slab_weight_shear_elasticity{W_s + E + ν}

    %% Edges
    density --> merge_slab_weight_inputs
    measured_layer_thickness --> merge_slab_weight_inputs
    merge_slab_weight_inputs -->|sum_layer_weight| slab_weight
    slab_weight --> merge_slab_weight_slope_angle
    measured_slope_angle --> merge_slab_weight_slope_angle
    merge_slab_weight_slope_angle -->|slope_parallel_component| slab_weight_shear
    slab_weight_shear --> merge_slab_weight_shear_elasticity
    elastic_modulus --> merge_slab_weight_shear_elasticity
    poissons_ratio --> merge_slab_weight_shear_elasticity
    merge_slab_weight_shear_elasticity -->|combine_shear_weight_and_elasticity| slab_weight_shear_with_elasticity

    %% Styling
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    class measured_slope_angle,measured_layer_thickness measuredNode
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    class merge_slab_weight_inputs,merge_slab_weight_slope_angle,merge_slab_weight_shear_elasticity mergeNode
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    class density,elastic_modulus,poissons_ratio layerCalc
    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px
    class slab_weight,slab_weight_shear,slab_weight_shear_with_elasticity slabCalc
```
