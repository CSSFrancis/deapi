"""
stem_viewer.py

A fast interactive 4D-STEM viewer for streaming data...

This is designed to be a simple viewer for a single image....
"""

import anywidget
import numpy as np
import traitlets
from deapi import ContrastStretchType

from deapi.client import Client
from deapi.data_types import FrameType, Attributes, PixelFormat


class SimpleViewer(anywidget.AnyWidget):
    """A simple viewer for a single image"""
    # Raw float32 frame as bytes (JS handles scale/colormap for real-time interactivity)
    frame_bytes = traitlets.Bytes(b"").tag(sync=True)
    det_x = traitlets.Int(512).tag(sync=True) # Size of the image data x
    det_y = traitlets.Int(512).tag(sync=True) # Size of the image data y
    shape_x = traitlets.Int(256).tag(sync=True)
    shape_y = traitlets.Int(256).tag(sync=True)

    raw_image_size_x = traitlets.Int(-1).tag(sync=True)  # Original image size x (for zoom/pan calculations)
    raw_image_size_y = traitlets.Int(-1).tag(sync=True)  # Original image size y (for zoom/pan calculations)

    pos_x = traitlets.Int(0).tag(sync=True)
    pos_y = traitlets.Int(0).tag(sync=True)
    roi_center_x = traitlets.Int(0).tag(sync=True)
    roi_center_y = traitlets.Int(0).tag(sync=True)

    histogram = traitlets.Bytes(b"").tag(sync=True)  # Optional: histogram data for JS colormap
    scale_x = traitlets.Float(1.0).tag(sync=True)  # Optional: scale for scale bar
    scale_y = traitlets.Float(1.0).tag(sync=True)  # Optional: scale for scale bar'
    units = traitlets.Unicode('px').tag(sync=True)

    window_width = traitlets.Int(450).tag(sync=True)
    window_height = traitlets.Int(450).tag(sync=True)

    # Zoom and pan controls
    zoom = traitlets.Float(1.0).tag(sync=True)
    center_x = traitlets.Float(.5).tag(sync=True)
    center_y = traitlets.Float(.5).tag(sync=True)

    # Scale bar configuration
    scalebar_location = traitlets.Unicode('bottom right').tag(sync=True)  # Options: 'bottom', 'top', 'top left', 'top right', 'bottom left', 'bottom right', 'off'

    _esm = """
    console.log('SimpleViewer module loading...');
    function render({ model, el }) {
      // Create canvases
      const dpCanvas = document.createElement('canvas');

      dpCanvas.width = model.get('window_width');
      dpCanvas.height = model.get('window_height');
      dpCanvas.style.border = '1px solid #444';

      // Create toolbar container (vertical, to the right of canvas)
      const toolbar = document.createElement('div');
      toolbar.style.position = 'relative';
      toolbar.style.display = 'flex';
      toolbar.style.flexDirection = 'column';
      toolbar.style.gap = '8px';
      toolbar.style.padding = '10px';
      toolbar.style.opacity = '0';
      toolbar.style.transition = 'opacity 0.2s ease';
      toolbar.style.minWidth = '60px';
      toolbar.style.alignItems = 'center';

      // Create reset view button
      const resetButton = document.createElement('button');
      resetButton.textContent = '🔄';
      resetButton.title = 'Reset View (Zoom 1.0x, Center) - Press R';
      resetButton.style.padding = '10px 14px';
      resetButton.style.fontSize = '18px';
      resetButton.style.cursor = 'pointer';
      resetButton.style.background = 'rgba(255, 255, 255, 0.95)';
      resetButton.style.border = '1px solid #ccc';
      resetButton.style.borderRadius = '4px';
      resetButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
      resetButton.style.width = '100%';

      // Create zoom display
      const zoomDisplay = document.createElement('div');
      zoomDisplay.style.padding = '8px 12px';
      zoomDisplay.style.fontSize = '13px';
      zoomDisplay.style.fontFamily = 'monospace';
      zoomDisplay.style.fontWeight = 'bold';
      zoomDisplay.style.background = 'rgba(0, 0, 0, 0.75)';
      zoomDisplay.style.color = 'white';
      zoomDisplay.style.borderRadius = '4px';
      zoomDisplay.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
      zoomDisplay.style.textAlign = 'center';
      zoomDisplay.style.width = '100%';
      zoomDisplay.textContent = `${model.get('zoom').toFixed(2)}x`;

      toolbar.appendChild(resetButton);
      toolbar.appendChild(zoomDisplay);

      // Create resize handle
      const resizeHandle = document.createElement('div');
      resizeHandle.style.position = 'absolute';
      resizeHandle.style.bottom = '5px';
      resizeHandle.style.right = '1px';
      resizeHandle.style.width = '16px';
      resizeHandle.style.height = '16px';
      resizeHandle.style.cursor = 'nwse-resize';
      resizeHandle.style.background = 'linear-gradient(135deg, transparent 0%, transparent 50%, #888 50%, #888 100%)';
      resizeHandle.style.borderRadius = '0 0 2px 0';
      resizeHandle.title = 'Drag to resize';

      // Size label
      const sizeLabel = document.createElement('div');
      sizeLabel.style.position = 'absolute';
      sizeLabel.style.bottom = '20px';
      sizeLabel.style.right = '20px';
      sizeLabel.style.padding = '4px 8px';
      sizeLabel.style.background = 'rgba(0, 0, 0, 0.7)';
      sizeLabel.style.color = 'white';
      sizeLabel.style.fontSize = '12px';
      sizeLabel.style.borderRadius = '4px';
      sizeLabel.style.display = 'none';
      sizeLabel.style.pointerEvents = 'none';
      sizeLabel.textContent = `${model.get('window_width')} × ${model.get('window_height')}`;

      // Scale bar overlay - container with transparent background
      const scaleBar = document.createElement('div');
      scaleBar.style.position = 'absolute';
      scaleBar.style.background = 'rgba(0, 0, 0, 0.5)';
      scaleBar.style.padding = '4px 8px';
      scaleBar.style.borderRadius = '4px';
      scaleBar.style.boxShadow = '0 2px 4px rgba(0,0,0,0.4)';
      scaleBar.style.pointerEvents = 'none';
      
      const scaleBarLine = document.createElement('div');
      scaleBarLine.style.background = 'white';
      scaleBarLine.style.height = '4px';
      scaleBarLine.style.width = '100px';
      scaleBarLine.style.marginBottom = '2px';
      
      const scaleBarLabel = document.createElement('div');
      scaleBarLabel.style.color = 'white';
      scaleBarLabel.style.fontSize = '11px';
      scaleBarLabel.style.fontWeight = 'bold';
      scaleBarLabel.style.textAlign = 'center';
      scaleBarLabel.textContent = '100 nm';
      
      scaleBar.appendChild(scaleBarLine);
      scaleBar.appendChild(scaleBarLabel);
      
      // Function to find a nice round number close to the target
      function findNiceNumber(target) {
        if (target <= 0) return 1;
        
        // Nice numbers to use
        const niceNumbers = [1, 2, 3, 5, 7, 10];
        
        // Find the appropriate order of magnitude
        const magnitude = Math.pow(10, Math.floor(Math.log10(target)));
        
        // Find the best nice number at this magnitude
        let bestValue = magnitude;
        let bestDiff = Math.abs(target - bestValue);
        
        for (const nice of niceNumbers) {
          const value = nice * magnitude;
          const diff = Math.abs(target - value);
          if (diff < bestDiff) {
            bestValue = value;
            bestDiff = diff;
          }
        }
        
        // Also check the next magnitude up
        for (const nice of [1, 2, 3, 5]) {
          const value = nice * magnitude * 10;
          const diff = Math.abs(target - value);
          if (diff < bestDiff) {
            bestValue = value;
            bestDiff = diff;
          }
        }
        
        return bestValue;
      }
      
      // Helper function to format values nicely (handle large/small numbers)
      function formatValue(value) {
        if (value >= 1000) {
          return (value / 1000).toFixed(value / 1000 >= 10 ? 0 : 1);
        } else if (value >= 100) {
          return value.toFixed(0);
        } else if (value >= 10) {
          return value.toFixed(0);
        } else if (value >= 1) {
          return value.toFixed(1);
        } else {
          return value.toFixed(2);
        }
      }
      
      // Scale bar update function - calculates proper size based on zoom and physical/pixel units
      function drawScaleBar() {
        const zoom = model.get('zoom');
        const scale_x = model.get('scale_x');
        const units = model.get('units');
        const windowWidth = model.get('window_width');
        
        // Calculate target scale bar width (about 1/4 of the image width)
        const targetBarWidthPx = windowWidth / 4;
        
        // Determine if we're using pixel units (fallback) or physical units
        const usePixels = !scale_x || scale_x <= 0;
        
        if (usePixels) {
          // Fallback to pixels
          const det_x = model.get('det_x');
          
          // Calculate how many pixels correspond to targetBarWidthPx on screen
          // Taking zoom into account: at zoom 1.0, windowWidth pixels = det_x data pixels
          const pixelsPerScreenPixel = det_x / windowWidth;
          const targetPixels = targetBarWidthPx * pixelsPerScreenPixel / zoom;
          
          // Find a nice round number
          const niceValue = findNiceNumber(targetPixels);
          
          // Calculate the actual bar width in screen pixels
          const actualBarWidthPx = (niceValue / pixelsPerScreenPixel) * zoom;
          
          scaleBarLine.style.width = actualBarWidthPx + 'px';
          scaleBarLabel.textContent = niceValue + ' px';
        } else {
          // Use physical units
          // scale_x is in units per pixel (e.g., nm/pixel)
          // Calculate physical size that corresponds to targetBarWidthPx on screen
          const det_x = model.get('det_x');
          const pixelsPerScreenPixel = det_x / windowWidth;
          const targetDataPixels = targetBarWidthPx * pixelsPerScreenPixel / zoom;
          const targetPhysicalSize = targetDataPixels * scale_x;
          
          // Find a nice round number for the physical size
          const niceValue = findNiceNumber(targetPhysicalSize);
          
          // Calculate the actual bar width in screen pixels
          const actualDataPixels = niceValue / scale_x;
          const actualBarWidthPx = (actualDataPixels / pixelsPerScreenPixel) * zoom;
          
          scaleBarLine.style.width = actualBarWidthPx + 'px';
          scaleBarLabel.textContent = formatValue(niceValue) + ' ' + units;
        }
      }
      
      // Function to update scale bar position based on scalebar_location
      function updateScaleBarPosition() {
        const location = model.get('scalebar_location').toLowerCase();
        
        if (location === 'off') {
          scaleBar.style.display = 'none';
          return;
        }
        
        scaleBar.style.display = 'block';
        
        // Reset all positioning
        scaleBar.style.top = 'auto';
        scaleBar.style.bottom = 'auto';
        scaleBar.style.left = 'auto';
        scaleBar.style.right = 'auto';
        scaleBar.style.transform = 'none';
        
        const margin = 15;
        
        if (location === 'bottom right') {
          scaleBar.style.bottom = margin + 'px';
          scaleBar.style.right = margin + 'px';
        } else if (location === 'bottom left') {
          scaleBar.style.bottom = margin + 'px';
          scaleBar.style.left = margin + 'px';
        } else if (location === 'top right') {
          scaleBar.style.top = margin + 'px';
          scaleBar.style.right = margin + 'px';
        } else if (location === 'top left') {
          scaleBar.style.top = margin + 'px';
          scaleBar.style.left = margin + 'px';
        } else if (location === 'bottom') {
          scaleBar.style.bottom = margin + 'px';
          scaleBar.style.left = '50%';
          scaleBar.style.transform = 'translateX(-50%)';
        } else if (location === 'top') {
          scaleBar.style.top = margin + 'px';
          scaleBar.style.left = '50%';
          scaleBar.style.transform = 'translateX(-50%)';
        }
        
        drawScaleBar();  // Update scale bar content after repositioning
      }
      
      updateScaleBarPosition();

      // Layout - horizontal container with canvas and toolbar side by side
      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.flexDirection = 'row';
      container.style.gap = '0';
      container.style.alignItems = 'flex-start';
      
      const canvasWrapper = document.createElement('div');
      canvasWrapper.style.position = 'relative';
      canvasWrapper.style.display = 'inline-block';
      
      canvasWrapper.appendChild(dpCanvas);
      canvasWrapper.appendChild(resizeHandle);
      canvasWrapper.appendChild(sizeLabel);
      canvasWrapper.appendChild(scaleBar);
      
      container.appendChild(canvasWrapper);
      container.appendChild(toolbar);
      
      // Show/hide toolbar on hover over the entire container
      container.addEventListener('mouseenter', () => {
        toolbar.style.opacity = '1';
      });
      
      container.addEventListener('mouseleave', () => {
        toolbar.style.opacity = '0';
      });
      
      el.appendChild(container);

      console.log('SimpleViewer module Loaded successfully');

      let animationId = null;
      let isResizing = false;
      let isPanning = false;
      let startX, startY, startWidth, startHeight;
      let panStartX, panStartY, panStartCenterX, panStartCenterY;
      let lastPanUpdate = 0;

      // Resize handle drag functionality
      resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = dpCanvas.width;
        startHeight = dpCanvas.height;
        sizeLabel.style.display = 'block';
        e.preventDefault();
      });

      document.addEventListener('mousemove', (e) => {
        if (isResizing) {
          const deltaX = e.clientX - startX;
          const deltaY = e.clientY - startY;
          
          // Get raw image dimensions for aspect ratio
          const rawImageX = model.get('raw_image_size_x');
          const rawImageY = model.get('raw_image_size_y');
          
          let newWidth, newHeight;
          
          if (rawImageX > 0 && rawImageY > 0) {
            // Maintain aspect ratio based on raw image dimensions
            const aspectRatio = rawImageX / rawImageY;
            
            // Use the average delta to determine the new size
            const avgDelta = (deltaX + deltaY) / 2;
            newWidth = Math.max(128, startWidth + avgDelta);
            newHeight = Math.max(128, newWidth / aspectRatio);
            
            // Ensure minimum size for both dimensions
            if (newHeight < 128) {
              newHeight = 128;
              newWidth = newHeight * aspectRatio;
            }
          } else {
            // Fallback to free resize if raw dimensions not available
            newWidth = Math.max(128, startWidth + deltaX);
            newHeight = Math.max(128, startHeight + deltaY);
          }
          
          // Update canvas size immediately for visual feedback
          dpCanvas.width = newWidth;
          dpCanvas.height = newHeight;
          sizeLabel.textContent = `${Math.round(newWidth)} × ${Math.round(newHeight)}`;
          
          e.preventDefault();
        } else if (isPanning) {
          const rect = dpCanvas.getBoundingClientRect();
          const deltaX = (e.clientX - panStartX) / rect.width;
          const deltaY = (e.clientY - panStartY) / rect.height;

          const currentZoom = model.get('zoom');
          const newCenterX = panStartCenterX - deltaX / currentZoom;
          const newCenterY = panStartCenterY - deltaY / currentZoom;

          // Throttle updates to every 100ms
          const now = Date.now();
          if (!lastPanUpdate || now - lastPanUpdate > 100) {
            model.set('center_x', Math.max(0, Math.min(1, newCenterX)));
            model.set('center_y', Math.max(0, Math.min(1, newCenterY)));
            model.save_changes();
            lastPanUpdate = now;
          }

          e.preventDefault();
        }
      });

      document.addEventListener('mouseup', (e) => {
        if (isResizing) {
          isResizing = false;
          sizeLabel.style.display = 'none';
          
          // Round dimensions and update model with final size (this will trigger Python to fetch new image)
          const finalWidth = Math.round(dpCanvas.width);
          const finalHeight = Math.round(dpCanvas.height);
          model.set('window_width', finalWidth);
          model.set('window_height', finalHeight);
          model.save_changes();
          
          console.log('Resize complete:', finalWidth, 'x', finalHeight);
        }
        if (isPanning) {
          isPanning = false;
          dpCanvas.style.cursor = 'default';
          
          // Send final position update
          const rect = dpCanvas.getBoundingClientRect();
          const deltaX = (e.clientX - panStartX) / rect.width;
          const deltaY = (e.clientY - panStartY) / rect.height;
          const currentZoom = model.get('zoom');
          const newCenterX = panStartCenterX - deltaX / currentZoom;
          const newCenterY = panStartCenterY - deltaY / currentZoom;
          
          model.set('center_x', Math.max(0, Math.min(1, newCenterX)));
          model.set('center_y', Math.max(0, Math.min(1, newCenterY)));
          model.save_changes();
          
          console.log('Pan complete');
        }
      });

      // Handle window size changes from Python
      model.on('change:window_width', () => {
        dpCanvas.width = model.get('window_width');
        console.log('Canvas width changed:', model.get('window_width'));
        drawScaleBar();  // Redraw scale bar when window width changes
      });

      model.on('change:window_height', () => {
        dpCanvas.height = model.get('window_height');
        console.log('Canvas height changed:', model.get('window_height'));
      });

      // Reset view button handler
      resetButton.addEventListener('click', () => {
        model.set('zoom', 1.0);
        model.set('center_x', 0.5);
        model.set('center_y', 0.5);
        model.save_changes();
        console.log('View reset');
      });

      // Keyboard shortcut: press 'r' to reset view
      document.addEventListener('keydown', (e) => {
        if (e.key === 'r' || e.key === 'R') {
          model.set('zoom', 1.0);
          model.set('center_x', 0.5);
          model.set('center_y', 0.5);
          model.save_changes();
          console.log('View reset via keyboard (R key)');
        }
      });


      // Update zoom display
      model.on('change:zoom', () => {
        zoomDisplay.textContent = `${model.get('zoom').toFixed(2)}x`;
        drawScaleBar();  // Redraw scale bar when zoom changes
      });

      // Update scale bar position when scalebar_location changes
      model.on('change:scalebar_location', () => {
        updateScaleBarPosition();
      });

      // Redraw scale bar when scale or image dimensions change
      model.on('change:scale_x', () => {
        drawScaleBar();
      });

      model.on('change:det_x', () => {
        drawScaleBar();
      });
      
      model.on('change:units', () => {
        drawScaleBar();
      });
      
      model.on('change:window_width', () => {
        drawScaleBar();
      });

      // Listen to Python model changes
      model.on('change:frame_bytes', () => {
        console.log('frame_bytes changed');
        const grayscaleBytes = new Uint8Array(model.get('frame_bytes').buffer);
        console.log('length:', grayscaleBytes.length);
        console.log('det_x:', model.get('det_x'), 'det_y:', model.get('det_y'));

        const ctx = dpCanvas.getContext('2d');
        const width = model.get('det_x');
        const height = model.get('det_y');
        const imageData = ctx.createImageData(width, height);

        console.log('Expected bytes:', width * height);
        console.log('Actual bytes:', grayscaleBytes.length);

        // Convert grayscale to RGBA in JavaScript
        const rgba = imageData.data;
        for (let i = 0; i < grayscaleBytes.length; i++) {
          const gray = grayscaleBytes[i];
          const idx = i * 4;
          rgba[idx] = gray;     // R
          rgba[idx + 1] = gray; // G
          rgba[idx + 2] = gray; // B
          rgba[idx + 3] = 255;  // A
        }

        ctx.putImageData(imageData, 0, 0);
        console.log('Image updated successfully');
      });

      model.on('change:det_x', () => {
        console.log('det_x changed:', model.get('det_x'));
      });

      dpCanvas.addEventListener('click', (e) => {
        if (isPanning) return; // Don't trigger click if we were panning
        console.log('Canvas clicked at:', e.clientX, e.clientY);
        const rect = dpCanvas.getBoundingClientRect();
        const kx = Math.floor((e.clientX - rect.left) / rect.width * model.get('det_x'));
        const ky = Math.floor((e.clientY - rect.top) / rect.height * model.get('det_y'));
        model.set('roi_center_x', kx);
        model.set('roi_center_y', ky);
        model.save_changes();
      });

      // Mouse wheel zoom (zoom in/out centered on mouse position)
      dpCanvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        const rect = dpCanvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) / rect.width;
        const mouseY = (e.clientY - rect.top) / rect.height;
        
        const currentZoom = model.get('zoom');
        const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1; // Scroll down = zoom out, scroll up = zoom in
        const newZoom = Math.max(0.1, Math.min(100, currentZoom * zoomDelta));
        
        // Adjust center to zoom towards mouse position
        const currentCenterX = model.get('center_x');
        const currentCenterY = model.get('center_y');
        
        // Calculate new center to keep mouse position fixed
        const dx = mouseX - 0.5;
        const dy = mouseY - 0.5;
        const zoomRatio = currentZoom / newZoom;
        
        const newCenterX = currentCenterX + dx * (1 - zoomRatio) / newZoom;
        const newCenterY = currentCenterY + dy * (1 - zoomRatio) / newZoom;
        
        model.set('zoom', newZoom);
        model.set('center_x', Math.max(0, Math.min(1, newCenterX)));
        model.set('center_y', Math.max(0, Math.min(1, newCenterY)));
        model.save_changes();
        
        console.log('Zoom:', newZoom, 'Center:', newCenterX, newCenterY);
      });

      // Mouse drag to pan
      dpCanvas.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return; // Only left mouse button
        isPanning = true;
        panStartX = e.clientX;
        panStartY = e.clientY;
        panStartCenterX = model.get('center_x');
        panStartCenterY = model.get('center_y');
        dpCanvas.style.cursor = 'grabbing';
        e.preventDefault();
      });
    }

    export default { render };
    """

    def __init__(self,
                 client: Client,
                 image: str | FrameType):
        super().__init__()
        self.client = client
        if isinstance(image, str):
            image = FrameType.__getitem__(image.upper())
        self.image = image
        self._stop_loop = False
        self.observe(self._on_window_size_changed, names=['window_width', 'window_height'])
        self.observe(self._on_zoom_pan_changed, names=['zoom', 'center_x', 'center_y'])
        self._update_image()
        self._start_auto_update_loop()

    def _on_zoom_pan_changed(self, change):
        """Update image when zoom or pan changes"""
        if hasattr(self, 'client'):
            self._update_image()

    def _on_window_size_changed(self, change):
        """Update canvas size when window dimensions change"""
        # Force a re-render by updating the image
        if hasattr(self, 'client'):
            self._update_image()

    def _start_auto_update_loop(self):
        """Start a background loop that checks if client is acquiring and updates accordingly"""
        import asyncio

        async def auto_update_loop():
            print("Auto-update loop started - checking acquisition state every 0.5s")
            last_image_hash = None

            while not self._stop_loop:
                try:
                    is_acquiring = self.client.acquiring

                    if is_acquiring:
                        # Client is acquiring - update continuously at ~30 FPS
                        print("Acquisition detected - streaming updates")
                        while self.client.acquiring and not self._stop_loop:
                            img = self._update_image()

                            # Check if image has changed
                            if img is not None:
                                current_hash = hash(img.tobytes())
                                if current_hash == last_image_hash:
                                    # Image hasn't changed, check if acquisition stopped
                                    if not self.client.acquiring:
                                        print("Acquisition stopped - returning to poll mode")
                                        break
                                else:
                                    last_image_hash = current_hash

                            await asyncio.sleep(0.033)  # ~30 FPS
                    else:
                        # Not acquiring - check every 0.5 seconds
                        await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error in auto-update loop: {e}")
                    await asyncio.sleep(0.5)

        # Try to get or create event loop and schedule the task
        try:
            # Try to get the running event loop (Jupyter, IPython)
            loop = asyncio.get_running_loop()
            # Schedule the coroutine as a task
            asyncio.create_task(auto_update_loop())
            print("Auto-update loop scheduled in existing event loop")
        except RuntimeError:
            # No event loop running - create one and run in thread
            import threading

            def run_async_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(auto_update_loop())

            threading.Thread(target=run_async_loop, daemon=True).start()
            print("Auto-update loop started in new thread with asyncio")

    def get_raw_image_size(self):
        if (FrameType.VIRTUAL_IMAGE0.value <= self.image.value <= FrameType.VIRTUAL_IMAGE4.value or
            FrameType.EXTERNAL_IMAGE1.value <= self.image.value <= FrameType.EXTERNAL_IMAGE4.value):
            self.raw_image_size_x = self.client["Scan - Size X"]
            self.raw_image_size_y = self.client["Scan - Size Y"]
        else:
            self.raw_image_size_x = self.client["Image Size X (pixels)"]
            self.raw_image_size_y = self.client["Image Size Y (pixels)"]

    def get_scale(self):
        try:
            if (FrameType.VIRTUAL_IMAGE0.value <= self.image.value <= FrameType.VIRTUAL_IMAGE4.value or
                FrameType.EXTERNAL_IMAGE1.value <= self.image.value <= FrameType.EXTERNAL_IMAGE4.value):
                # Diffraction pattern - use mrad units
                self.scale_x = self.client["Diffraction Pixel Size X"]
                self.scale_y = self.client["Diffraction Pixel Size Y"]
                self.units = "mrad" if self.scale_x > 0 else "px"
            else:
                # Real space image - use nm units
                self.scale_x = self.client["Specimen Pixel Size X (nanometers)"]
                self.scale_y = self.client["Specimen Pixel Size Y (nanometers)"]
                self.units = "nm" if self.scale_x > 0 else "px"
        except (KeyError, AttributeError, TypeError) as e:
            # If scale information is not available, fall back to pixels
            print(f"Scale information not available: {e}. Using pixels.")
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.units = "px"


    def _update_image(self):
        """Called to update the image"""

        self.get_raw_image_size()
        self.get_scale()

        if self.raw_image_size_x == -1:
            cx = 0
        else:
            cx = int(self.center_x * self.raw_image_size_x)
            if cx <1:
                cx = 1
        if self.raw_image_size_y == -1:
            cy = 0
        else:
            cy = int(self.center_y * self.raw_image_size_y)
            if cy <1:
                cy = 1
        a = Attributes(
            window_width=self.window_width,
            window_height=self.window_height,
            zoom=self.zoom,
            center_x=cx,
            center_y=cy,
            stretch_type=ContrastStretchType.LINEAR,
        )

        result = self.client.get_result(self.image, attributes=a, pixel_format=PixelFormat.UINT8)
        # Server handles contrast stretching based on stretch_type, returns uint8 directly


        img = result.image

        if img is None:
            print("No image data received from client.")
            return 0

        # Server should return uint8 when we request UINT8 dtype
        # If not, convert without naive rescaling
        if img.dtype != np.uint8:
            # Use percentile-based scaling to avoid overexposure from hot pixels
            p_low, p_high = np.percentile(img, [1, 99])
            img_clipped = np.clip(img, p_low, p_high)
            img = ((img_clipped - p_low) / (p_high - p_low) * 255).astype(np.uint8)

        # Handle multi-channel images by converting to grayscale
        if len(img.shape) == 3:
            # If RGBA or RGB, convert to grayscale
            if img.shape[2] == 4 or img.shape[2] == 3:
                img = img[:, :, 0]  # Use only the first channel

        # Ensure we have a 2D grayscale image
        if len(img.shape) != 2:
            print(f"Warning: Unexpected image shape {img.shape}")
            return None

        # Batch all updates together
        with self.hold_trait_notifications():
            self.det_x = img.shape[1]
            self.det_y = img.shape[0]
            self.frame_bytes = img.tobytes()
        return img
