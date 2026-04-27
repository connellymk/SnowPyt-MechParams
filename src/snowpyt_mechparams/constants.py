"""
Physical constants and reference values for snow mechanical parameter calculations.

This module contains:
- Physical constants (ice properties)
- Field measurement mappings (hand hardness)
- Method validation constraints (grain form codes)
"""

from typing import Optional

# ==========================================
# Physical Constants for Ice
# ==========================================

# Density of ice (kg/m³)
# Standard reference value used across multiple parameterizations
RHO_ICE = 917.0  # kg/m³

# Young's modulus of bulk polycrystalline ice (MPa)
# Standard value assumed by the FE simulations underlying Köchle & Schneebeli (2014)
# and used for normalisation in Schöttner et al. (2026).
# NOTE: In the kochle method this constant is introduced by this repository to cast
# the original absolute-value formula into a dimensionless form; E_ice cancels
# algebraically (C_2 = C_0/E_ice, then E_snow = E_ice * C_2 * exp(...)), so the
# choice of value does not affect the output. It must still match the assumption
# made when the empirical C_0 constants were fit (10 GPa) to keep the algebra
# self-consistent.
E_ICE_POLYCRYSTALLINE: float = 10000.0  # MPa (10 GPa)

# Shear modulus of ice (MPa)
# Derived from E_ICE_POLYCRYSTALLINE via G = E / (2 * (1 + ν)) with ν_ice = 0.3:
# G = 10000 / (2 * 1.3) ≈ 3846.15 MPa.
G_ICE: float = 3846.15  # MPa

# Standard gravitational acceleration (m/s²)
# Used in gravitational shear stress calculations (Roch criterion, WEAC inputs).
g: float = 9.81  # m/s²


# ==========================================
# Standard Measurement Uncertainties
# ==========================================

# Hand hardness index measurement uncertainty: ±2 subclasses = ±0.67 HHI units
U_HAND_HARDNESS_INDEX = 0.67

# Slope angle measurement uncertainty: ±2° (degrees)
U_SLOPE_ANGLE = 2.0  # degrees

# Grain size measurement uncertainty: ±0.5 mm
U_GRAIN_SIZE = 0.5  # mm

# Layer thickness measurement uncertainty: ±5% (relative, multiply by measured value)
U_THICKNESS_FRACTION = 0.05  # 5%

# Density measurement uncertainty: ±10% (relative, multiply by measured value)
U_DENSITY_FRACTION = 0.10  # 10%


# ==========================================
# Field Measurement Mappings
# ==========================================

# Map hand hardness string to numeric hand hardness index (hhi)
# Based on standard snow profile measurement techniques
HARDNESS_MAPPING = {
    "F-": 0.67,
    "F": 1.0,
    "F+": 1.33,  # Fist
    "4F-": 1.67,
    "4F": 2.0,
    "4F+": 2.33,  # Four Fingers
    "1F-": 2.67,
    "1F": 3.0,
    "1F+": 3.33,  # One Finger
    "P-": 3.67,
    "P": 4.0,
    "P+": 4.33,  # Pencil
    "K-": 4.67,
    "K": 5.0,
    "K+": 5.33,  # Knife
}


# ==========================================
# Method Validation Constraints
# ==========================================

# Grain form codes organized by method
# Defines which grain forms are valid for each density calculation method
GRAIN_FORM_METHODS = {
    "geldsetzer": {
        "sub_grain_class": {"PPgp"},
        "basic_grain_class": {"PP", "DF", "RG", "FC", "DH"},
    },
    "kim_jamieson_table2": {
        "sub_grain_class": {"PPgp", "RGxf", "FCxr", "MFcr"},
        "basic_grain_class": {"PP", "DF", "FC", "DH", "RG"},
    },
    "kim_jamieson_table5": {
        "sub_grain_class": {"FCxr", "PPgp"},
        "basic_grain_class": {"FC", "PP", "DF", "MF"},
    },
}


def resolve_grain_form_for_method(
    grain_form: Optional[str], method: str
) -> Optional[str]:
    """
    Resolve which grain form code to use for a given density method.

    This is the single source of truth for grain form validation logic.
    It tries the full grain_form first (which could be a sub-grain code like 'FCxr'),
    then falls back to the basic grain class (first 2 characters like 'RG').

    Parameters
    ----------
    grain_form : Optional[str]
        The grain form code to resolve. Can be either:
        - A 2-character basic grain class code (e.g., 'RG', 'FC', 'PP')
        - A longer sub-grain class code (e.g., 'RGxf', 'FCxr', 'PPgp')
        - None
    method : str
        The density estimation method name. Should be one of the keys in
        GRAIN_FORM_METHODS: 'geldsetzer', 'kim_jamieson_table2', 'kim_jamieson_table5'

    Returns
    -------
    Optional[str]
        The grain form code to use for the method's lookup table, or None if:
        - grain_form is None
        - method is not recognized (returns grain_form unchanged)
        - grain_form cannot be mapped to any valid code for this method

    Examples
    --------
    >>> resolve_grain_form_for_method('PPgp', 'geldsetzer')
    'PPgp'  # Sub-grain code is valid for this method

    >>> resolve_grain_form_for_method('RGxf', 'geldsetzer')
    'RG'  # Sub-grain code not valid, falls back to basic class

    >>> resolve_grain_form_for_method('FC', 'kim_jamieson_table5')
    'FC'  # Basic code is valid

    >>> resolve_grain_form_for_method('DH', 'kim_jamieson_table5')
    None  # DH not valid for this method

    Notes
    -----
    This function is used by:
    - dispatcher._resolve_grain_form() for Layer objects
    - snowpilot_convert.convert_grain_form() for CAAML grain form objects
    """
    if not grain_form:
        return None

    # Normalize method name to lowercase
    method_lower = method.lower()

    # If method not recognized, return grain_form as-is (let caller decide)
    if method_lower not in GRAIN_FORM_METHODS:
        return grain_form

    valid_codes = GRAIN_FORM_METHODS[method_lower]

    # Try full grain_form first (could be a sub-grain code)
    if grain_form in valid_codes["sub_grain_class"]:
        return grain_form

    if grain_form in valid_codes["basic_grain_class"]:
        return grain_form

    # Fall back to basic grain class (first 2 characters)
    if len(grain_form) >= 2:
        basic_code = grain_form[:2]
        if basic_code in valid_codes["basic_grain_class"]:
            return basic_code

    # No valid mapping found
    return None


# ==========================================
# Stability Criterion Constants
# ==========================================

# Standard skier mass used in stability criteria (kg).
# Reference: Föhn (1987); used as default in WEAC skier variant.
STANDARD_SKIER_MASS_KG = 80.0

# ==========================================
# Weak Layer Definitions
# ==========================================

# Valid weak layer definitions for Pit.create_slabs()
# These define how to identify weak layers when creating slab objects from pit data
WEAK_LAYER_DEFINITIONS = ["layer_of_concern", "CT_failure_layer", "ECTP_failure_layer"]
