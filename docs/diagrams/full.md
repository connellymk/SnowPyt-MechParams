# SnowPyt-MechParams — Full Parameter Graph

```mermaid
graph LR

    subgraph INPUTS["Snow Pit Observations"]
    snow_pit[snow pit]
    measured_density[density (measured)]
    measured_hand_hardness[hand hardness]
    measured_grain_form[grain form]
    measured_grain_size[grain size]
    measured_layer_thickness[layer thickness]
    end

    subgraph LAYER_MERGES["Layer Merge Nodes"]
    merge_hand_hardness_grain_form{HH + grain form}
    merge_hand_hardness_grain_form_grain_size{HH + grain form + size}
    merge_density_grain_form{ρ + grain form}
    end

    subgraph LAYER["Layer Parameters"]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    end

    subgraph SLAB_MERGES["Slab Merge Nodes"]
    merge_E_nu{E + ν (all layers)}
    merge_zi_E_nu{z_i + E + ν}
    merge_hi_G{h_i + G (all layers)}
    merge_hi_E_nu{h_i + E + ν}
    end

    subgraph SLAB["Slab Stiffnesses"]
    D11[D11]
    B11[B11]
    A11[A11]
    A55[A55]
    end

    subgraph WEAKLAYER["Weak-Layer Parameters"]
    G_c[G_c]
    G_Ic[G_Ic]
    G_IIc[G_IIc]
    sigma_c[σ_c]
    tau_c[τ_c]
    sigma_comp[σ_comp]
    end

    subgraph STABILITY["Stability Criteria"]
    merge_weac_inputs{WEAC inputs}
    merge_roch_inputs{Roch inputs}
    g_delta[g_Δ (WEAC)]
    s_r[S_r (Roch natural)]
    end

    %% Edges
    snow_pit --> measured_density
    snow_pit --> measured_hand_hardness
    snow_pit --> measured_grain_form
    snow_pit --> measured_grain_size
    snow_pit --> measured_layer_thickness
    measured_density --> density
    measured_hand_hardness --> merge_hand_hardness_grain_form
    measured_grain_form --> merge_hand_hardness_grain_form
    merge_hand_hardness_grain_form -->|G09| density
    merge_hand_hardness_grain_form -->|KJ-t2| density
    merge_hand_hardness_grain_form --> merge_hand_hardness_grain_form_grain_size
    measured_grain_size --> merge_hand_hardness_grain_form_grain_size
    merge_hand_hardness_grain_form_grain_size -->|KJ-t5| density
    density --> merge_density_grain_form
    measured_grain_form --> merge_density_grain_form
    merge_density_grain_form -->|B23| elastic_modulus
    merge_density_grain_form -->|K14| elastic_modulus
    merge_density_grain_form -->|W15| elastic_modulus
    merge_density_grain_form -->|S26| elastic_modulus
    measured_grain_form -->|K14| poissons_ratio
    merge_density_grain_form -->|Sr16| poissons_ratio
    merge_density_grain_form -->|W15| shear_modulus
    snow_pit -->|W&R| G_c
    snow_pit -->|W&R| G_Ic
    snow_pit -->|W&R| G_IIc
    snow_pit -->|W&R| sigma_c
    snow_pit -->|W&R| tau_c
    snow_pit -->|R15| sigma_comp
    density -->|Sg06| sigma_c
    density -->|M75| sigma_comp
    density --> merge_weac_inputs
    elastic_modulus --> merge_weac_inputs
    poissons_ratio --> merge_weac_inputs
    shear_modulus --> merge_weac_inputs
    measured_layer_thickness --> merge_weac_inputs
    G_c --> merge_weac_inputs
    G_Ic --> merge_weac_inputs
    G_IIc --> merge_weac_inputs
    sigma_c --> merge_weac_inputs
    tau_c --> merge_weac_inputs
    sigma_comp --> merge_weac_inputs
    merge_weac_inputs -->|WEAC| g_delta
    density --> merge_roch_inputs
    measured_layer_thickness --> merge_roch_inputs
    tau_c --> merge_roch_inputs
    merge_roch_inputs -->|Roch-n| s_r
    measured_layer_thickness --> merge_zi
    elastic_modulus --> merge_E_nu
    poissons_ratio --> merge_E_nu
    merge_zi --> merge_zi_E_nu
    merge_E_nu --> merge_zi_E_nu
    measured_layer_thickness --> merge_hi_G
    shear_modulus --> merge_hi_G
    measured_layer_thickness --> merge_hi_E_nu
    merge_E_nu --> merge_hi_E_nu
    merge_zi_E_nu -->|W&R| D11
    merge_hi_G -->|W&R| A55
    merge_hi_E_nu -->|W&R| A11
    merge_hi_E_nu -->|W&R| B11

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
    class merge_hand_hardness_grain_form,merge_hand_hardness_grain_form_grain_size,merge_density_grain_form,merge_zi,merge_E_nu,merge_zi_E_nu,merge_hi_G,merge_hi_E_nu,merge_weac_inputs,merge_roch_inputs mergeNode
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
    class A11,B11,D11,A55 slabCalc
    class G_c,G_Ic,G_IIc,sigma_c,tau_c,sigma_comp weakLayerCalc
    class g_delta,s_r stabilityCalc
```
