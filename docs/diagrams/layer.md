# SnowPyt-MechParams — Layer Parameters

```mermaid
graph TB

    snow_pit[snow pit]
    measured_density[density (measured)]
    measured_hand_hardness[hand hardness]
    measured_grain_form[grain form]
    measured_grain_size[grain size]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    merge_hand_hardness_grain_form{HH + grain form}
    merge_hand_hardness_grain_form_grain_size{HH + grain form + size}
    merge_density_grain_form{ρ + grain form}
    merge_elastic_modulus_poissons_ratio{E + ν (layer)}

    %% Edges
    snow_pit --> measured_density
    snow_pit --> measured_hand_hardness
    snow_pit --> measured_grain_form
    snow_pit --> measured_grain_size
    measured_density --> density
    measured_hand_hardness --> merge_hand_hardness_grain_form
    measured_grain_form --> merge_hand_hardness_grain_form
    merge_hand_hardness_grain_form -->|geldsetzer| density
    merge_hand_hardness_grain_form -->|kim_jamieson_table2| density
    merge_hand_hardness_grain_form --> merge_hand_hardness_grain_form_grain_size
    measured_grain_size --> merge_hand_hardness_grain_form_grain_size
    merge_hand_hardness_grain_form_grain_size -->|kim_jamieson_table5| density
    density --> merge_density_grain_form
    measured_grain_form --> merge_density_grain_form
    merge_density_grain_form -->|bergfeld| elastic_modulus
    merge_density_grain_form -->|kochle| elastic_modulus
    merge_density_grain_form -->|wautier| elastic_modulus
    merge_density_grain_form -->|schottner| elastic_modulus
    measured_grain_form -->|kochle| poissons_ratio
    merge_density_grain_form -->|srivastava| poissons_ratio
    elastic_modulus --> merge_elastic_modulus_poissons_ratio
    poissons_ratio --> merge_elastic_modulus_poissons_ratio
    merge_elastic_modulus_poissons_ratio -->|lame_relationship| shear_modulus

    %% Styling
    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    class snow_pit rootNode
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    class measured_density,measured_hand_hardness,measured_grain_form,measured_grain_size measuredNode
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    class merge_hand_hardness_grain_form,merge_hand_hardness_grain_form_grain_size,merge_density_grain_form,merge_elastic_modulus_poissons_ratio mergeNode
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
```
