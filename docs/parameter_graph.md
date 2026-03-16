# SnowPyt-MechParams Parameter Graph

```mermaid
graph TB
    %% Root node
    snow_pit[snow_pit<br/>ROOT]
    
    %% Measured parameter nodes
    measured_density[measured_density<br/>MEASURED]
    measured_hand_hardness[measured_hand_hardness<br/>MEASURED]
    measured_grain_form[measured_grain_form<br/>MEASURED]
    measured_grain_size[measured_grain_size<br/>MEASURED]
    measured_layer_thickness[measured_layer_thickness<br/>MEASURED]
    
    %% Layer-level merge nodes
    merge_hand_hardness_grain_form{merge_hand<br/>_hardness<br/>_grain<br/>_form}
    merge_hand_hardness_grain_form_grain_size{merge_hand<br/>_hardness<br/>_grain<br/>_form<br/>_grain<br/>_size}
    merge_density_grain_form{merge_density<br/>_grain<br/>_form}
    
    %% Calculated layer parameters
    density[density<br/>CALCULATED]
    elastic_modulus[elastic_modulus<br/>CALCULATED]
    poissons_ratio[poissons_ratio<br/>CALCULATED]
    shear_modulus[shear_modulus<br/>CALCULATED]
    
    %% Slab-level merge nodes
    zi{zi<br/>spatial info}
    merge_E_nu{merge_E<br/>_nu}
    merge_zi_E_nu{merge_zi<br/>_E<br/>_nu}
    merge_hi_G{merge_hi<br/>_G}
    merge_hi_E_nu{merge_hi<br/>_E<br/>_nu}
    
    %% Slab parameters
    A11[A11<br/>Extensional Stiffness<br/>SLAB]
    B11[B11<br/>Bending-Extension Coupling<br/>SLAB]
    D11[D11<br/>Bending Stiffness<br/>SLAB]
    A55[A55<br/>Shear Stiffness<br/>SLAB]
    
    %% Weak-layer parameters
    G_c[G_c<br/>WEAK_LAYER_CALC]
    G_Ic[G_Ic<br/>WEAK_LAYER_CALC]
    G_IIc[G_IIc<br/>WEAK_LAYER_CALC]
    sigma_c[sigma_c<br/>WEAK_LAYER_CALC]
    tau_c[tau_c<br/>WEAK_LAYER_CALC]
    sigma_comp[sigma_comp<br/>WEAK_LAYER_CALC]
    
    %% Stability merge nodes
    merge_weac_inputs{merge_weac<br/>_inputs}
    merge_roch_inputs{merge_roch<br/>_inputs}
    
    %% Stability model outputs
    g_delta[g_delta<br/>STABILITY_CALC]
    s_r[s_r<br/>STABILITY_CALC]
    s_sk[s_sk<br/>STABILITY_CALC]
    
    %% All parameter relationships
    snow_pit --> measured_density
    snow_pit --> measured_hand_hardness
    snow_pit --> measured_grain_form
    snow_pit --> measured_grain_size
    snow_pit --> measured_layer_thickness
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
    merge_density_grain_form -->|wautier| shear_modulus
    snow_pit -->|weissgraeber_rosendahl| G_c
    snow_pit -->|weissgraeber_rosendahl| G_Ic
    snow_pit -->|weissgraeber_rosendahl| G_IIc
    snow_pit -->|weissgraeber_rosendahl| sigma_c
    snow_pit -->|weissgraeber_rosendahl| tau_c
    snow_pit -->|weissgraeber_rosendahl| sigma_comp
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
    measured_layer_thickness --> zi
    elastic_modulus --> merge_E_nu
    poissons_ratio --> merge_E_nu
    zi --> merge_zi_E_nu
    merge_E_nu --> merge_zi_E_nu
    measured_layer_thickness --> merge_hi_G
    shear_modulus --> merge_hi_G
    measured_layer_thickness --> merge_hi_E_nu
    merge_E_nu --> merge_hi_E_nu
    merge_zi_E_nu -->|weissgraeber_rosendahl| D11
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
    
    class snow_pit rootNode
    class measured_density,measured_hand_hardness,measured_grain_form,measured_grain_size,measured_layer_thickness measuredNode
    class merge_hand_hardness_grain_form,merge_hand_hardness_grain_form_grain_size,merge_density_grain_form,zi,merge_E_nu,merge_zi_E_nu,merge_hi_G,merge_hi_E_nu,merge_weac_inputs,merge_roch_inputs mergeNode
    class density,elastic_modulus,poissons_ratio,shear_modulus layerCalc
    class A11,B11,D11,A55 slabCalc
    class G_c,G_Ic,G_IIc,sigma_c,tau_c,sigma_comp weakLayerCalc
    class g_delta,s_r,s_sk stabilityCalc
```
