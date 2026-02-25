"""
====================================
Live Visualization with ResultViewer
====================================

This example demonstrates how to use ``Client.get_live_result()`` for real-time
acquisition visualization. The ResultViewer automatically updates at ~30 FPS
during active acquisition.

Features:
    * Live image updates during acquisition
    * Interactive zoom and pan with mouse
    * Toggle histogram visibility with 'h' key
    * Reset view with 'r' key
    * State persistence across kernel restarts
    * Multiple frame type support

"""

# %%
# Setup and Connection
# ====================
#
# First, import the required modules and connect to the DE Server.

from deapi import Client
from deapi.widget import ResultViewer

# Connect to DE Server
client = Client()
client.connect()

print("✓ Connected to DE Server")
print(f"Acquiring: {client.acquiring}")

print("✓ Connected to DE Server")
print(f"Acquiring: {client.acquiring}")

# %%
# Basic Live Viewer
# =================
#
# Create a simple live viewer without histogram. The viewer automatically
# updates when the client is acquiring data.
#
# **Interactive controls:**
#
# * Mouse wheel: Zoom in/out
# * Click + drag: Pan around image
# * Press 'r': Reset view to default zoom/pan
# * Hover over image: Focus canvas (green outline appears)

viewer = client.get_live_result()

viewer

# %%
# Display the viewer
# In Jupyter: display(viewer)
# The viewer will update automatically at ~30 FPS during acquisition

print("Basic live viewer created")
print("- Updates automatically during acquisition")
print("- Mouse wheel to zoom, click+drag to pan")
print("- Press 'r' to reset view")

# %%
# Live Viewer with Histogram
# ===========================
#
# Create a viewer with a live histogram displayed side-by-side with the image.
# The histogram updates in sync with the image data.
#
# **Additional controls:**
#
# * Press 'h': Toggle histogram visibility
# * The histogram shows the intensity distribution in real-time

viewer_with_hist = client.get_live_result(display_histogram=True)

print("Live viewer with histogram created")
print("- Press 'h' to toggle histogram visibility")
print("- Histogram updates in sync with image")

viewer_with_hist
# %%
# Custom Configuration
# ====================
#
# Customize the viewer appearance and behavior by modifying its properties.

viewer_custom = client.get_live_result(display_histogram=True)

# Customize display size
viewer_custom.viewer_width = 600
viewer_custom.viewer_height = 600

# Enable log scale for histogram
viewer_custom.log_scale = True

# Move scale bar to top left
viewer_custom.scalebar_location = 'top left'

# Show colorbar on histogram
viewer_custom.show_colorbar = True

print("Custom configuration applied:")
print(f"  Size: {viewer_custom.viewer_width}x{viewer_custom.viewer_height}")
print(f"  Log scale: {viewer_custom.log_scale}")
print(f"  Scale bar: {viewer_custom.scalebar_location}")

viewer_custom

# %%
# Different Frame Types
# =====================
#
# View different types of frames: integrated images, virtual detector images,
# or diffraction patterns.

# Integrated frame (default)
integrated = client.get_live_result("singleframe_integrated", display_histogram=True)
integrated.viewer_width = 400
integrated.viewer_height = 400

# Virtual detector image
virtual0 = client.get_live_result("virtual_image0", display_histogram=True)
virtual0.viewer_width = 400
virtual0.viewer_height = 400

print("Multiple viewers created:")
print("  1. Integrated frame")
print("  2. Virtual detector image")
print("\nIn Jupyter, display both with:")
print("  display(integrated, virtual0)")

# %%
# Programmatic Control
# ====================
#
# Control zoom, pan, and other settings programmatically.

viewer_prog = client.get_live_result(display_histogram=True)

# Set zoom level
viewer_prog.zoom = 2.0

# Pan to specific position (0.0 to 1.0)
viewer_prog.center_x = 0.3
viewer_prog.center_y = 0.7

# Toggle histogram
viewer_prog.histogram_visible = False

print("Programmatic control applied:")
print(f"  Zoom: {viewer_prog.zoom}x")
print(f"  Center: ({viewer_prog.center_x}, {viewer_prog.center_y})")
print(f"  Histogram visible: {viewer_prog.histogram_visible}")

viewer_prog
# %%
# Tips and Best Practices
# ========================
#
# **Keyboard Shortcuts** (canvas must be focused):
#
# * Press 'h': Toggle histogram visibility
# * Press 'r': Reset view (zoom 1.0x, centered)
#
# **Mouse Controls:**
#
# * Mouse wheel: Zoom in/out (centered on cursor position)
# * Click + drag: Pan around the image
# * Drag corner handle: Resize viewer
#
# **Focusing the Canvas:**
#
# * Hover mouse over the image to focus it
# * Green outline indicates canvas is focused
# * Keyboard shortcuts only work when focused
#
# **Performance Tips:**
#
# * Smaller viewer size = faster updates
# * Hide histogram if not needed: ``viewer.histogram_visible = False``
# * Log scale can improve contrast in histogram
#


