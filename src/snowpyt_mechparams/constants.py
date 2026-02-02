"""
Physical constants and reference values for snow mechanical parameter calculations.

This module contains constants used across multiple calculation methods,
including material properties of ice and field measurement mappings.
"""

# Physical Constants for Ice
# ---------------------------

# Density of ice (kg/m³)
# Standard reference value used across multiple parameterizations
RHO_ICE = 917.0  # kg/m³


# Field Measurement Mappings
# ---------------------------

# Map hand hardness string to numeric hand hardness index (hhi)
# Based on standard snow profile measurement techniques
HARDNESS_MAPPING = {
    'F-': 0.67, 'F': 1.0, 'F+': 1.33,      # Fist
    '4F-': 1.67, '4F': 2.0, '4F+': 2.33,   # Four Fingers
    '1F-': 2.67, '1F': 3.0, '1F+': 3.33,   # One Finger
    'P-': 3.67, 'P': 4.0, 'P+': 4.33,      # Pencil
    'K-': 4.67, 'K': 5.0, 'K+': 5.33       # Knife
}
