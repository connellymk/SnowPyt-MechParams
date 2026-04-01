# SnowPyt-MechParams — Overview

```mermaid
graph LR

    subgraph INPUTS[Snow Pit Observations]
        meas_density[density]
        meas_hh[hand hardness]
        meas_gf[grain form]
        meas_gs[grain size]
        meas_thick[layer thickness]
    end

    subgraph LAYER[Layer Parameters]
        rho[ρ — density]
        E[E — elastic modulus]
        nu[ν — Poisson's ratio]
        G[G — shear modulus]
    end

    subgraph SLAB[Slab Stiffnesses]
        A11[A11]
        B11[B11]
        D11[D11]
        A55[A55]
    end

    subgraph WEAKLAYER[Weak-Layer Info]
        wl_info[weak layer info* — placeholder]
    end

    subgraph STABILITY[Stability Criteria]
        elast[slab elasticity params — E + ν]
        gdelta[g_Δ — WEAC skier]
        sr[S_r — Roch natural]
    end

    %% Group-level data flow
    INPUTS --> LAYER
    LAYER --> SLAB
    LAYER --> STABILITY
    WEAKLAYER --> STABILITY

    %% Styling
    classDef inputGroup fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef layerGroup fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef slabGroup fill:#ffccbc,stroke:#d84315,stroke-width:3px
    classDef wlGroup fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef stabGroup fill:#fce4ec,stroke:#880e4f,stroke-width:3px
    
    class meas_density,meas_hh,meas_gf,meas_gs,meas_thick inputGroup
    class rho,E,nu,G layerGroup
    class A11,B11,D11,A55 slabGroup
    class wl_info wlGroup
    class elast,gdelta,sr stabGroup
```
