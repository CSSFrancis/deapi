from deapi.client import Client
from deapi.version import version as __version__

from deapi.data_types import (
    FrameType,
    PixelFormat,
    DataType,
    MovieBufferStatus,
    MovieBufferInfo,
    VirtualMask,
    ContrastStretchType,
    Attributes,
    Histogram,
    PropertySpec,
    PropertyCollection,
)

# Automatically enable property and action widgets if Panel is installed
try:
    import panel as pn
    from deapi.panel import enable_property_widgets, enable_action_widgets
    enable_property_widgets(Client)
    enable_action_widgets(Client)
    _PANEL_AVAILABLE = True
except ImportError:
    _PANEL_AVAILABLE = False


__all__ = [
    "Client",
    "__version__",
    "FrameType",
    "PixelFormat",
    "DataType",
    "MovieBufferStatus",
    "MovieBufferInfo",
    "VirtualMask",
    "ContrastStretchType",
    "Attributes",
    "Histogram",
    "PropertySpec",
    "PropertyCollection",
]
