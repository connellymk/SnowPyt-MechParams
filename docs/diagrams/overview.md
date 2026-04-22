# SnowPyt-MechParams — Overview

```mermaid
graph LR

    subgraph INPUTS[Snow Pit Observations]
    measured_density[density (measured)]
    measured_hand_hardness[hand hardness]
    measured_grain_form[grain form]
    measured_grain_size[grain size]
    measured_slope_angle[slope angle]
    measured_layer_thickness[layer thickness]
    end

    subgraph LAYER[Layer Parameters]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    end

    subgraph SLAB[Slab Stiffnesses]
    A11[A11]
    B11[B11]
    D11[D11]
    A55[A55]
    end

    subgraph WEIGHT[Slab Weight Pathways]
    slab_weight[slab weight (W)]
    slab_weight_shear[slab weight_shear (W_s)]
    slab_weight_with_elasticity[slab weight with elasticity]
    end

    %% Group-level data flow
    INPUTS --> LAYER
    LAYER --> SLAB
    INPUTS --> SLAB
    INPUTS --> WEIGHT
    LAYER --> WEIGHT

    %% Styling
    classDef inputGroup fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef layerGroup fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef slabGroup fill:#ffccbc,stroke:#d84315,stroke-width:3px
    classDef weightGroup fill:#fce4ec,stroke:#880e4f,stroke-width:3px
    
    class measured_density,measured_hand_hardness,measured_grain_form,measured_grain_size,measured_slope_angle,measured_layer_thickness inputGroup
    class density,elastic_modulus,poissons_ratio,shear_modulus layerGroup
    class A11,B11,D11,A55 slabGroup
    class slab_weight,slab_weight_shear,slab_weight_with_elasticity weightGroup
```
