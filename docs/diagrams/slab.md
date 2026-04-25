# SnowPyt-MechParams — Slab Stiffnesses

```mermaid
graph LR

    measured_layer_thickness[layer thickness]
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
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    class measured_layer_thickness measuredNode
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    class merge_E_nu,merge_hi_G,merge_hi_E_nu mergeNode
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    class elastic_modulus,poissons_ratio,shear_modulus layerCalc
    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px
    class A11,B11,D11,A55 slabCalc
```
