# SnowPyt-MechParams — Slab Stiffnesses

```mermaid
graph LR

    measured_layer_thickness[layer thickness]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    A11[A11]
    B11[B11]
    D11[D11]
    A55[A55]
    merge_E_nu{E + ν (all layers)}
    merge_hi_G{h_i + G (all layers)}
    merge_hi_E_nu{h_i + E + ν}

    %% Edges
    elastic_modulus --> merge_E_nu
    poissons_ratio --> merge_E_nu
    measured_layer_thickness --> merge_hi_G
    shear_modulus --> merge_hi_G
    measured_layer_thickness --> merge_hi_E_nu
    merge_E_nu --> merge_hi_E_nu
    merge_hi_E_nu -->|weissgraeber_rosendahl| D11
    merge_hi_G -->|weissgraeber_rosendahl| A55
    merge_hi_E_nu -->|weissgraeber_rosendahl| A11
    merge_hi_E_nu -->|weissgraeber_rosendahl| B11

    %% Styling
    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px
    classDef weakLayerCalc fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef stabilityCalc fill:#fce4ec,stroke:#880e4f,stroke-width:3px
    
    class measured_layer_thickness measuredNode
    class merge_E_nu,merge_hi_G,merge_hi_E_nu mergeNode
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
    class A11,B11,D11,A55 slabCalc
```
