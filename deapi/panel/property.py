"""
Property widget for editing DE Server properties in Panel/Jupyter

This module provides an interactive widget system for editing properties
on the DE Server with automatic synchronization and live updates.

Example
-------
>>> from deapi import Client
>>> client = Client('localhost')
>>> widget = client["Frames Per Second"].widget
>>> widget  # Display in Jupyter
"""

import panel as pn
import asyncio
from typing import Optional, Callable
import logging

pn.extension()

log = logging.getLogger("deapi.panel")


class PropertyWidget(pn.Column):
    """Interactive widget for a DE Server property

    This widget provides a GUI control for editing a server property with:
    - Automatic type detection (int, float, string, enum)
    - Range validation based on property specs
    - Bidirectional sync with server (updates every second)
    - Immediate updates when value is changed locally

    Parameters
    ----------
    client : Client
        The DE Client instance
    property_name : str
        The name of the property to control
    update_interval : float, optional
        How often to poll the server for updates (seconds), by default 1.0

    Attributes
    ----------
    widget : pn.Column
        The Panel widget that can be displayed

    Examples
    --------
    >>> from deapi import Client
    >>> client = Client('localhost')
    >>> fps_widget = PropertyWidget(client, "Frames Per Second")
    >>> fps_widget  # Display in Jupyter - it's directly a Panel widget

    >>> # Or via PropertyProxy:
    >>> widget = client["Frames Per Second"].widget
    >>> widget  # Directly a Panel widget, can use in pn.Row(), pn.Column(), etc.
    """

    def __init__(
        self,
        client,
        property_name: str,
        update_interval: float = 1.0,
        on_change: Optional[Callable] = None,
        show_indicator: bool = False
    ):
        self.client = client
        self.property_name = property_name
        self.update_interval = update_interval
        self.on_change = on_change
        self.show_indicator = show_indicator
        self._updating_from_server = False
        self._stop_update = False

        # Get property specification
        self.spec = self._get_property_spec()

        # Create the appropriate widget based on property type
        self.control = self._create_control()

        # Create layout components
        self._create_components()

        # Initialize parent Column with the components
        if self.show_indicator and self.status:
            super().__init__(
                pn.Row(self.control, self.status, sizing_mode='stretch_width'),
                sizing_mode='stretch_width'
            )
        else:
            super().__init__(
                self.control,
                sizing_mode='stretch_width'
            )

        # Start async update loop
        self._start_update_loop()

    def _get_property_spec(self):
        """Get property specification from server"""
        try:
            # Try newer API first (DE-MC >= 2.7.4)
            spec = self.client.get_property_specifications(self.property_name)
        except:
            # Fall back to older API
            try:
                spec = self.client.get_property_spec(self.property_name)
            except Exception as e:
                log.warning(f"Could not get spec for {self.property_name}: {e}")
                # Create minimal spec
                from deapi.data_types import PropertySpec
                spec = PropertySpec(
                    data_type="String",
                    value_type="AllowAll",
                    current_value=str(self.client[self.property_name])
                )
        return spec

    def _parse_range(self, options):
        """Parse range from options list"""
        if len(options) >= 2:
            try:
                if self.spec.dataType == "Integer":
                    return int(options[0]), int(options[1])
                else:
                    return float(options[0]), float(options[1])
            except (ValueError, TypeError):
                return None, None
        return None, None

    def _create_control(self):
        """Create the appropriate Panel widget based on property type"""
        data_type = self.spec.dataType
        value_type = self.spec.valueType
        current_value = self.spec.currentValue
        options = self.spec.options if self.spec.options else []
        read_only = getattr(self.spec, 'read_only', False) or getattr(self.spec, 'readonly', False)

        # Define default widths based on type
        # Integers and floats: short (100px)
        # Strings: medium for single word (200px)
        # Dropdowns: auto-size based on content
        INT_WIDTH = 100
        FLOAT_WIDTH = 100
        STRING_WIDTH = 200

        # Parse current value
        try:
            if data_type == "Integer":
                current_value = int(float(current_value))
            elif data_type == "Float":
                current_value = float(current_value)
            else:
                current_value = str(current_value)
        except (ValueError, TypeError):
            current_value = str(current_value)

        # Create control based on type
        control = None

        if value_type == "Set" and options:
            # Dropdown/Select for enumerated values
            if isinstance(options, str):
                # Parse string representation of list
                options_list = [opt.strip().strip("'\"").rstrip('*') for opt in options.split(",")]
            else:
                options_list = [str(opt).strip().strip("'\"").rstrip('*') for opt in options]

            # Filter out empty strings
            options_list = [opt for opt in options_list if opt]

            # Strip asterisk from current value as well
            current_value = str(current_value).rstrip('*')

            # Auto-size dropdown based on longest option
            max_option_len = max([len(str(opt)) for opt in options_list]) if options_list else 10
            dropdown_width = min(max(max_option_len * 8 + 40, 120), 300)  # 8px per char, min 120, max 300

            control = pn.widgets.Select(
                name=self.property_name,
                options=options_list,
                value=str(current_value) if str(current_value) in options_list else (options_list[0] if options_list else ""),
                disabled=read_only,
                width=dropdown_width
            )

        elif value_type == "Range" and data_type in ["Integer", "Float"]:
            # Slider for numeric ranges
            min_val, max_val = self._parse_range(options)

            if min_val is not None and max_val is not None:
                if data_type == "Integer":
                    control = pn.widgets.IntSlider(
                        name=self.property_name,
                        start=min_val,
                        end=max_val,
                        value=int(current_value) if min_val <= int(current_value) <= max_val else min_val,
                        disabled=read_only,
                        width=200  # Sliders get slightly more width for better usability
                    )
                else:
                    control = pn.widgets.FloatSlider(
                        name=self.property_name,
                        start=min_val,
                        end=max_val,
                        value=float(current_value) if min_val <= float(current_value) <= max_val else min_val,
                        step=(max_val - min_val) / 100,
                        disabled=read_only,
                        width=200  # Sliders get slightly more width for better usability
                    )
            else:
                # No valid range, use input
                if data_type == "Integer":
                    control = pn.widgets.IntInput(
                        name=self.property_name,
                        value=int(current_value),
                        disabled=read_only,
                        width=INT_WIDTH
                    )
                else:
                    control = pn.widgets.FloatInput(
                        name=self.property_name,
                        value=float(current_value),
                        disabled=read_only,
                        width=FLOAT_WIDTH
                    )

        elif data_type == "Integer":
            # Integer input
            control = pn.widgets.IntInput(
                name=self.property_name,
                value=int(current_value),
                disabled=read_only,
                width=INT_WIDTH
            )

        elif data_type == "Float":
            # Float input
            control = pn.widgets.FloatInput(
                name=self.property_name,
                value=float(current_value),
                disabled=read_only,
                width=FLOAT_WIDTH
            )

        else:
            # Text input for everything else
            control = pn.widgets.TextInput(
                name=self.property_name,
                value=str(current_value),
                disabled=read_only,
                width=STRING_WIDTH
            )

        # Attach callback for value changes
        control.param.watch(self._on_value_change, 'value')

        return control

    def _create_components(self):
        """Create the status indicator component"""
        # Status indicator (only if show_indicator is True)
        if self.show_indicator:
            self.status = pn.indicators.LoadingSpinner(
                value=False,
                size=20,
                color='primary'
            )
        else:
            self.status = None


    def _on_value_change(self, event):
        """Callback when widget value changes"""
        if self._updating_from_server:
            return

        new_value = event.new

        # Show loading indicator if enabled
        if self.show_indicator and self.status:
            self.status.value = True

        try:
            # Set value on server
            self.client[self.property_name] = new_value
            log.info(f"Updated {self.property_name} to {new_value}")

            # Call user callback if provided
            if self.on_change:
                self.on_change(new_value)

        except Exception as e:
            log.error(f"Error setting {self.property_name}: {e}")
            # Revert to server value
            self._update_from_server()

        finally:
            if self.show_indicator and self.status:
                self.status.value = False

    def _update_from_server(self):
        """Update widget value from server"""
        try:
            self._updating_from_server = True

            # Get current value from server
            server_value = self.client[self.property_name]

            # Convert to appropriate type
            if self.spec.dataType == "Integer":
                server_value = int(float(server_value))
            elif self.spec.dataType == "Float":
                server_value = float(server_value)
            else:
                server_value = str(server_value)

            # Update control if value changed
            # For floats, always check since server value may differ from set value
            # For other types, only update if different
            if self.spec.dataType == "Float":
                # For floats, update if the difference is significant
                if self.control.value != server_value:
                    self.control.value = server_value
                    log.debug(f"Updated {self.property_name} from server: {server_value}")
            else:
                # For non-floats, only update if different
                if self.control.value != server_value:
                    self.control.value = server_value
                    log.debug(f"Updated {self.property_name} from server: {server_value}")

        except Exception as e:
            log.error(f"Error updating {self.property_name} from server: {e}")

        finally:
            self._updating_from_server = False

    def _start_update_loop(self):
        """Start the async update loop"""
        async def update_loop():
            while not self._stop_update:
                await asyncio.sleep(self.update_interval)
                self._update_from_server()

        # Schedule the coroutine
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run in background
        if loop.is_running():
            asyncio.create_task(update_loop())
        else:
            # If loop is not running, use panel's periodic callback
            pn.state.add_periodic_callback(
                self._update_from_server,
                period=int(self.update_interval * 1000),  # Convert to ms
                timeout=None
            )

    def stop(self):
        """Stop the update loop"""
        self._stop_update = True


class PropertyProxy:
    """Proxy object that provides access to both property value and widget

    This is returned by client[property_name] to provide convenient access to:
    - The property value (via __str__, __int__, __float__, etc.)
    - The widget (via .widget attribute)

    Examples
    --------
    >>> prop = client["Frames Per Second"]
    >>> print(prop)  # Gets current value
    >>> prop.widget  # Returns PropertyWidget for GUI editing
    >>> int(prop)    # Converts to int
    """

    def __init__(self, client, property_name: str):
        self._client = client
        self._property_name = property_name
        self._widget_instance = None

    @property
    def widget(self):
        """Get or create the property widget"""
        if self._widget_instance is None:
            self._widget_instance = PropertyWidget(self._client, self._property_name)
        return self._widget_instance

    def _get_value(self):
        """Get the current value from the client"""
        return self._client.get_property(self._property_name)

    def __str__(self):
        return str(self._get_value())

    def __repr__(self):
        return f"PropertyProxy('{self._property_name}', value={self._get_value()})"

    def __int__(self):
        return int(self._get_value())

    def __float__(self):
        return float(self._get_value())

    def __bool__(self):
        val = self._get_value()
        if isinstance(val, str):
            return val.lower() not in ['false', '0', '', 'no']
        return bool(val)

    def __eq__(self, other):
        return self._get_value() == other

    def __ne__(self, other):
        return self._get_value() != other

    def __lt__(self, other):
        return self._get_value() < other

    def __le__(self, other):
        return self._get_value() <= other

    def __gt__(self, other):
        return self._get_value() > other

    def __ge__(self, other):
        return self._get_value() >= other


    # Traitlets compatibility methods
    def __index__(self):
        """Support for integer indexing operations"""
        return int(self._get_value())

    def __hash__(self):
        """Make PropertyProxy hashable for use in sets/dicts"""
        return hash((self._property_name, self._get_value()))

    def __getattr__(self, name):
        """Delegate attribute access to the underlying value"""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._get_value(), name)


def enable_property_widgets(client_class):
    """Decorator/function to enable property widgets on a Client class

    This modifies the __getitem__ method to return PropertyProxy objects
    instead of raw values, enabling the .widget attribute.

    Parameters
    ----------
    client_class : class
        The Client class to modify

    Returns
    -------
    class
        The modified client class

    Examples
    --------
    >>> from deapi import Client
    >>> from deapi.panel.property import enable_property_widgets
    >>> enable_property_widgets(Client)
    >>> client = Client('localhost')
    >>> client["Frames Per Second"].widget  # Now works!
    """
    original_getitem = client_class.__getitem__

    def new_getitem(self, key):
        # Return PropertyProxy that has both value and .widget
        return PropertyProxy(self, key)

    client_class.__getitem__ = new_getitem

    # Also provide a way to get raw value
    def get_property_value(self, key):
        """Get raw property value without widget support"""
        return original_getitem(self, key)

    client_class.get_property_value = get_property_value

    return client_class

