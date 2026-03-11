# Data Structures UML Diagram

Mermaid UML diagram of the snow mechanical parameter data structures: `Layer`, `Pit`, and `Slab`.

```mermaid
classDiagram
    class Layer {
        <<dataclass>>
        +UncertainValue depth_top
        +UncertainValue thickness
        +UncertainValue density_measured
        +str hand_hardness
        +str grain_form
        +UncertainValue grain_size_avg
        +bool layer_of_concern
        +UncertainValue density_calculated
        +UncertainValue poissons_ratio
        +UncertainValue shear_modulus
        +UncertainValue elastic_modulus
        +depth_bottom() UncertainValue
        +hand_hardness_index() UncertainValue
        +main_grain_form() str
    }

    class Pit {
        <<dataclass>>
        +Any snow_pit
        +str pit_id
        +float slope_angle
        +List~Layer~ layers
        +List~Any~ ECT_results
        +List~Any~ CT_results
        +List~Any~ PST_results
        +from_snow_pit(snow_pit) Pit
        +layer_of_concern Layer
        +create_slabs(weak_layer_def) List~Slab~
    }

    class Slab {
        <<dataclass>>
        +List~Layer~ layers
        +UncertainValue angle
        +Layer weak_layer
        +Pit pit
        +str pit_id
        +str slab_id
        +str weak_layer_source
        +int test_result_index
        +dict test_result_properties
        +int n_test_results_in_pit
        +UncertainValue A11
        +UncertainValue A55
        +UncertainValue B11
        +UncertainValue D11
        +total_thickness() UncertainValue
    }

    Pit "1" *-- "0..*" Layer : contains
    Pit "1" o-- "0..*" Slab : creates
    Slab "1" *-- "1..*" Layer : layers
    Slab "1" --> "0..1" Layer : weak_layer
    Slab "1" --> "0..1" Pit : pit
```

## Relationships

| Relationship | Description |
|--------------|-------------|
| **Pit → Layer** | A `Pit` contains a list of `Layer` objects (composition). Layers are created from the snow profile via `_create_layers_from_profile()`. |
| **Pit → Slab** | A `Pit` creates one or more `Slab` objects via `create_slabs()`. Each slab corresponds to a weak layer identified by a test result or layer of concern. |
| **Slab → Layer** | A `Slab` contains an ordered list of `Layer` objects (the slab layers above the weak layer). |
| **Slab → weak_layer** | A `Slab` references a single `Layer` as its weak layer. |
| **Slab → Pit** | A `Slab` holds a reference back to its parent `Pit` for accessing test results and metadata. |

## Type Aliases

- **UncertainValue**: `Union[float, uncertainties.UFloat]` — values that can be regular floats or uncertain numbers for error propagation.
