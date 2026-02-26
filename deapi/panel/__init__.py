"""
Panel widgets for DE Server properties and actions

This module provides interactive Panel widgets for editing properties
and controlling actions on the DE Server with automatic synchronization.

Examples
--------
>>> from deapi import Client
>>>
>>> # Connect to server (widgets enabled automatically)
>>> client = Client('localhost')
>>>
>>> # Get property widget
>>> fps_widget = client["Frames Per Second"].widget
>>> fps_widget  # Display in Jupyter
>>>
>>> # Get action button widget
>>> start_button = client.start_acquisition.widget
>>> start_button  # Display in Jupyter
"""

from .property import PropertyWidget, PropertyProxy, enable_property_widgets
from .action import (
    ActionButtonWidget,
    StartStopButtonWidget,
    ActionProxy,
    enable_action_widgets
)

__all__ = [
    'PropertyWidget',
    'PropertyProxy',
    'enable_property_widgets',
    'ActionButtonWidget',
    'StartStopButtonWidget',
    'ActionProxy',
    'enable_action_widgets',
]

