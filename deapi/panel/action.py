"""
Action button widgets for DE Client methods

This module provides button widgets for client actions like start/stop acquisition.

Example
-------
>>> from deapi import Client
>>> client = Client('localhost')
>>>
>>> # Get start/stop button widget
>>> button = client.start_acquisition.widget
>>> button  # Display in Jupyter
"""

import panel as pn
from typing import Callable, Optional
import logging

pn.extension()

log = logging.getLogger("deapi.panel")


class ActionButtonWidget(pn.Row):
    """Button widget for a client action method

    This widget provides a button that calls a client method when clicked.
    Supports toggle buttons for start/stop pairs.

    Parameters
    ----------
    client : Client
        The DE Client instance
    method_name : str
        The name of the method to call
    button_label : str, optional
        Label for the button
    button_type : str, optional
        Panel button type: 'default', 'primary', 'success', 'warning', 'danger'
    width : int, optional
        Button width in pixels

    Examples
    --------
    >>> button = ActionButtonWidget(client, "start_acquisition", "Start")
    >>> button  # Display in Jupyter
    """

    def __init__(
        self,
        client,
        method_name: str,
        button_label: str = None,
        button_type: str = 'primary',
        width: int = 120,
        on_click: Optional[Callable] = None
    ):
        self.client = client
        self.method_name = method_name
        self.button_label = button_label or method_name.replace('_', ' ').title()
        self.on_click_callback = on_click

        # Create button
        self.button = pn.widgets.Button(
            name=self.button_label,
            button_type=button_type,
            width=width
        )

        # Attach click handler
        self.button.on_click(self._on_button_click)

        # Initialize parent Row with the button
        super().__init__(
            self.button,
            sizing_mode='fixed'
        )

    def _on_button_click(self, event):
        """Handle button click"""
        try:
            # Get the method from client
            method = getattr(self.client, self.method_name)

            # Call the method
            result = method()

            log.info(f"Called {self.method_name}(): {result}")

            # Call user callback if provided
            if self.on_click_callback:
                self.on_click_callback(result)

        except Exception as e:
            log.error(f"Error calling {self.method_name}(): {e}")

    def __repr__(self):
        return f"ActionButtonWidget(method='{self.method_name}')"


class StartStopButtonWidget(pn.Row):
    """Combined Start/Stop toggle button widget for acquisition control

    This widget provides a single button that toggles between Start and Stop states.
    When clicked, it calls client.start_acquisition() or client.stop_acquisition().

    The button automatically monitors the server's acquisition state every 0.5 seconds
    and updates the button state to match (Stop → Start when acquisition ends).

    Parameters
    ----------
    client : Client
        The DE Client instance
    width : int, optional
        Button width in pixels, by default 120
    on_start : Callable, optional
        Callback called when acquisition starts
    on_stop : Callable, optional
        Callback called when acquisition stops
    check_interval : float, optional
        How often to check acquisition status (seconds), by default 0.5

    Examples
    --------
    >>> button = StartStopButtonWidget(client)
    >>> button  # Display in Jupyter

    >>> # With callbacks
    >>> def on_start():
    ...     print("Acquisition started")
    >>> button = StartStopButtonWidget(client, on_start=on_start)
    """

    def __init__(
        self,
        client,
        width: int = 120,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        check_interval: float = 0.5
    ):
        self.client = client
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        self.check_interval = check_interval
        self._is_running = False
        self._stop_checking = False

        # Create button
        self.button = pn.widgets.Button(
            name='Start',
            button_type='success',
            width=width
        )

        # Attach click handler
        self.button.on_click(self._on_button_click)

        # Initialize parent Row with the button
        super().__init__(
            self.button,
            sizing_mode='fixed'
        )

        # Start acquisition status checking loop
        self._start_status_check()

    def _on_button_click(self, event):
        """Handle button click - toggle between start and stop"""
        try:
            if not self._is_running:
                # Start acquisition
                self.client.start_acquisition()
                self._is_running = True
                self.button.name = 'Stop'
                self.button.button_type = 'danger'
                log.info("Acquisition started")

                # Call user callback
                if self.on_start_callback:
                    self.on_start_callback()
            else:
                # Stop acquisition
                self.client.stop_acquisition()
                self._is_running = False
                self.button.name = 'Start'
                self.button.button_type = 'success'
                log.info("Acquisition stopped")

                # Call user callback
                if self.on_stop_callback:
                    self.on_stop_callback()

        except Exception as e:
            log.error(f"Error toggling acquisition: {e}")
            # Reset button state on error
            self._is_running = False
            self.button.name = 'Start'
            self.button.button_type = 'success'

    def _check_acquisition_status(self):
        """Check if server is still acquiring and update button state"""
        try:
            # Check if client has acquiring attribute
            if hasattr(self.client, 'acquiring'):
                is_acquiring = self.client.acquiring

                # If button thinks it's running but server says it's not
                if self._is_running and not is_acquiring:
                    self._is_running = False
                    self.button.name = 'Start'
                    self.button.button_type = 'success'

                # If button thinks it's stopped but server says it's running
                elif not self._is_running and is_acquiring:
                    log.info("Acquisition started (detected by status check)")
                    self._is_running = True
                    self.button.name = 'Stop'
                    self.button.button_type = 'danger'

        except Exception as e:
            log.debug(f"Error checking acquisition status: {e}")

    def _start_status_check(self):
        """Start the async status checking loop"""
        import asyncio

        async def status_check_loop():
            while not self._stop_checking:
                await asyncio.sleep(self.check_interval)
                self._check_acquisition_status()

        # Try to schedule the coroutine
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(status_check_loop())
                return
        except RuntimeError:
            pass  # No event loop yet

        except (RuntimeError, AttributeError):
            # Panel state not initialized or no event loop
            # Status checking will not work, but button will still function manually
            log.debug("Could not start automatic status checking (no event loop)")
            pass

    def stop(self):
        """Stop the status checking loop"""
        self._stop_checking = True


class ActionProxy:
    """Proxy object for client methods that provides .widget attribute

    This allows syntax like: client.start_acquisition.widget

    Parameters
    ----------
    client : Client
        The DE Client instance
    method_name : str
        The name of the method
    method : callable
        The actual method
    """

    def __init__(self, client, method_name: str, method: Callable):
        self._client = client
        self._method_name = method_name
        self._method = method
        self._widget_instance = None

    @property
    def widget(self):
        """Get or create the button widget for this action"""
        if self._widget_instance is None:
            # Special handling for start_acquisition - return start/stop toggle
            if self._method_name == 'start_acquisition':
                self._widget_instance = StartStopButtonWidget(self._client)
            else:
                # Generic button for other methods
                button_label = self._method_name.replace('_', ' ').title()
                self._widget_instance = ActionButtonWidget(
                    self._client,
                    self._method_name,
                    button_label=button_label
                )
        return self._widget_instance

    def __call__(self, *args, **kwargs):
        """Call the original method"""
        return self._method(*args, **kwargs)

    def __repr__(self):
        return f"ActionProxy(method='{self._method_name}')"


def enable_action_widgets(client_class):
    """Enable action button widgets on Client methods

    This wraps specific client methods (like start_acquisition, stop_acquisition)
    with ActionProxy objects that provide a .widget attribute.

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
    >>> from deapi.panel.action import enable_action_widgets
    >>> enable_action_widgets(Client)
    >>> client = Client('localhost')
    >>> client.start_acquisition.widget  # Now works!
    """

    # List of methods to wrap with widget support
    ACTION_METHODS = [
        'start_acquisition',
        'stop_acquisition',
    ]

    # Store original methods
    original_methods = {}
    for method_name in ACTION_METHODS:
        if hasattr(client_class, method_name):
            original_methods[method_name] = getattr(client_class, method_name)

    # Wrap __init__ to add proxies after initialization
    original_init = client_class.__init__

    def new_init(self, *args, **kwargs):
        # Call original init
        original_init(self, *args, **kwargs)

        # Wrap action methods with proxies
        for method_name, original_method in original_methods.items():
            # Bind the method to this instance
            bound_method = original_method.__get__(self, type(self))
            # Create proxy
            proxy = ActionProxy(self, method_name, bound_method)
            # Set as attribute
            setattr(self, method_name, proxy)

    client_class.__init__ = new_init

    return client_class

