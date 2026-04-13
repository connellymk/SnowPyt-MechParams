# SnowPyt-MechParams — Slab Elasticity Coverage & Stability Criteria

```mermaid
graph LR

    snow_pit[snow pit]
    measured_density[density (measured)]
    measured_hand_hardness[hand hardness]
    measured_grain_form[grain form]
    measured_grain_size[grain size]
    measured_layer_thickness[layer thickness]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    weak_layer_info*[weak layer info* (placeholder)]
    slab_elasticity_parameters{slab elasticity (E + ν)}
    g_delta[g_Δ (WEAC)]
    s_r[S_r (Roch natural)]
    merge_weac_inputs{WEAC inputs}
    merge_roch_inputs{Roch inputs}

    %% Edges
    snow_pit --> measured_density
    snow_pit --> measured_hand_hardness
    snow_pit --> measured_grain_form
    snow_pit --> measured_grain_size
    snow_pit --> measured_layer_thickness
    measured_density --> density
    measured_grain_form -->|kochle| poissons_ratio
    elastic_modulus --> slab_elasticity_parameters
    poissons_ratio --> slab_elasticity_parameters
    slab_elasticity_parameters --> merge_weac_inputs
    density --> merge_weac_inputs
    measured_layer_thickness --> merge_weac_inputs
    weak_layer_info* --> merge_weac_inputs
    merge_weac_inputs -->|weac_skier| g_delta
    density --> merge_roch_inputs
    measured_layer_thickness --> merge_roch_inputs
    weak_layer_info* --> merge_roch_inputs
    merge_roch_inputs -->|roch_natural| s_r

    %% Styling
    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px
    classDef weakLayerCalc fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef stabilityCalc fill:#fce4ec,stroke:#880e4f,stroke-width:3px
    
    class snow_pit rootNode
    class measured_density,measured_hand_hardness,measured_grain_form,measured_grain_size,measured_layer_thickness measuredNode
    class slab_elasticity_parameters,merge_weac_inputs,merge_roch_inputs mergeNode
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
    class weak_layer_info* weakLayerCalc
    class g_delta,s_r stabilityCalc
```
