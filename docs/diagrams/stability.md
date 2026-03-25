# SnowPyt-MechParams — Weak-Layer Parameters & Stability Criteria

```mermaid
graph LR

    snow_pit[snow pit]
    measured_density[density (measured)]
    measured_hand_hardness[hand hardness]
    measured_grain_form[grain form]
    measured_grain_size[grain size]
    density[ρ (density)]
    elastic_modulus[E (elastic modulus)]
    poissons_ratio[ν (Poisson's ratio)]
    shear_modulus[G (shear modulus)]
    G_c[G_c]
    G_Ic[G_Ic]
    G_IIc[G_IIc]
    sigma_c[σ_c]
    tau_c[τ_c]
    sigma_comp[σ_comp]
    density_weak_layer[ρ (weak-layer density)]
    merge_wl_hand_hardness_grain_form{WL: HH + grain form}
    merge_wl_hand_hardness_grain_form_grain_size{WL: HH + grain form + size}
    g_delta[g_Δ (WEAC)]
    merge_weac_inputs{WEAC inputs}
    s_r[S_r (Roch natural)]
    s_sk[S_sk (Roch skier)]
    merge_roch_inputs{Roch inputs}

    %% Edges
    snow_pit --> measured_density
    snow_pit --> measured_hand_hardness
    snow_pit --> measured_grain_form
    snow_pit --> measured_grain_size
    measured_density --> density
    measured_grain_form -->|kochle| poissons_ratio
    snow_pit -->|weissgraeber_rosendahl| G_c
    snow_pit -->|weissgraeber_rosendahl| G_Ic
    snow_pit -->|weissgraeber_rosendahl| G_IIc
    snow_pit -->|weissgraeber_rosendahl| sigma_c
    snow_pit -->|weissgraeber_rosendahl| tau_c
    snow_pit -->|reiweger| sigma_comp
    measured_hand_hardness --> merge_wl_hand_hardness_grain_form
    measured_grain_form --> merge_wl_hand_hardness_grain_form
    merge_wl_hand_hardness_grain_form -->|geldsetzer| density_weak_layer
    merge_wl_hand_hardness_grain_form -->|kim_jamieson_table2| density_weak_layer
    merge_wl_hand_hardness_grain_form --> merge_wl_hand_hardness_grain_form_grain_size
    measured_grain_size --> merge_wl_hand_hardness_grain_form_grain_size
    merge_wl_hand_hardness_grain_form_grain_size -->|kim_jamieson_table5| density_weak_layer
    measured_density --> density_weak_layer
    density_weak_layer -->|sigrist| sigma_c
    density_weak_layer -->|mellor| sigma_comp
    density --> merge_weac_inputs
    elastic_modulus --> merge_weac_inputs
    poissons_ratio --> merge_weac_inputs
    shear_modulus --> merge_weac_inputs
    G_c --> merge_weac_inputs
    G_Ic --> merge_weac_inputs
    G_IIc --> merge_weac_inputs
    sigma_c --> merge_weac_inputs
    tau_c --> merge_weac_inputs
    sigma_comp --> merge_weac_inputs
    merge_weac_inputs -->|weac_skier| g_delta
    density --> merge_roch_inputs
    tau_c --> merge_roch_inputs
    merge_roch_inputs -->|roch_natural| s_r
    merge_roch_inputs -->|roch_skier| s_sk

    %% Styling
    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px
    classDef weakLayerCalc fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef stabilityCalc fill:#fce4ec,stroke:#880e4f,stroke-width:3px
    
    class snow_pit rootNode
    class measured_density,measured_hand_hardness,measured_grain_form,measured_grain_size measuredNode
    class merge_wl_hand_hardness_grain_form,merge_wl_hand_hardness_grain_form_grain_size,merge_weac_inputs,merge_roch_inputs mergeNode
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
    class G_c,G_Ic,G_IIc,sigma_c,tau_c,sigma_comp,density_weak_layer weakLayerCalc
    class g_delta,s_r,s_sk stabilityCalc
```
