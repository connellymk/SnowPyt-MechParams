# Shared type aliases for snow mechanical parameter calculations

from typing import Union

import uncertainties

# Type alias for values that can be floats or uncertain numbers
UncertainValue = Union[float, uncertainties.UFloat]
