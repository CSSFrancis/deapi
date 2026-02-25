"""
result_viewer.py

A unified widget that displays an image viewer with an optional vertical histogram on the right.
Supports both static (Result) and dynamic (Client + FrameType) image sources.
"""

import anywidget
import numpy as np
import traitlets
from typing import Optional, Union


class ResultViewer(anywidget.AnyWidget):
    """A unified widget that combines image viewing and histogram display

    Features:
    - Static mode: Display a Result object
    - Dynamic mode: Live updates from Client + FrameType
    - Interactive zoom and pan with mouse wheel and drag
    - Toggle histogram visibility with 'h' key
    - Reset view with 'r' key
    - Single resize handle at bottom-right
    - Scale bar support

    Parameters
    ----------
    result : Result, optional
        A Result object for static display
    client : Client, optional
        A Client instance for dynamic updates
    image : str or FrameType, optional
        Frame type to display when using dynamic mode
    """

    # Image data
    image_bytes = traitlets.Bytes(b"").tag(sync=True)
    image_width = traitlets.Int(512).tag(sync=True)
    image_height = traitlets.Int(512).tag(sync=True)

    # Raw image dimensions (for zoom/pan calculations in dynamic mode)
    raw_image_size_x = traitlets.Int(-1).tag(sync=True)
    raw_image_size_y = traitlets.Int(-1).tag(sync=True)

    # Histogram data
    histogram_data = traitlets.Unicode('{"bins": [], "counts": []}').tag(sync=True)
    hist_min = traitlets.Float(0.0).tag(sync=True)
    hist_max = traitlets.Float(255.0).tag(sync=True)
    hist_bins = traitlets.Int(256).tag(sync=True)

    # Display settings
    viewer_width = traitlets.Int(512).tag(sync=True)
    viewer_height = traitlets.Int(512).tag(sync=True)
    histogram_width = traitlets.Int(120).tag(sync=True)
    gap = traitlets.Int(10).tag(sync=True)

    # Histogram display options
    log_scale = traitlets.Bool(False).tag(sync=True)
    show_colorbar = traitlets.Bool(True).tag(sync=True)
    colorbar_width = traitlets.Int(20).tag(sync=True)
    histogram_visible = traitlets.Bool(True).tag(sync=True)

    # Scale information
    scale_x = traitlets.Float(1.0).tag(sync=True)
    scale_y = traitlets.Float(1.0).tag(sync=True)
    units = traitlets.Unicode('px').tag(sync=True)
    scalebar_location = traitlets.Unicode('bottom right').tag(sync=True)

    # Zoom and pan
    zoom = traitlets.Float(1.0).tag(sync=True)
    center_x = traitlets.Float(0.5).tag(sync=True)
    center_y = traitlets.Float(0.5).tag(sync=True)

    _esm = """
    console.log('ResultViewer module loading...');
    
    function render({ model, el }) {
      const dpr = window.devicePixelRatio || 1;
      
      // Create outer container
      const outerContainer = document.createElement('div');
      outerContainer.style.position = 'relative';
      outerContainer.style.display = 'inline-block';
      
      // Create main container
      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.flexDirection = 'row';
      container.style.gap = model.get('gap') + 'px';
      container.style.background = '#f5f5f5';
      container.style.padding = '10px';
      container.style.borderRadius = '4px';
      container.style.position = 'relative';
      
      let viewerWidth = model.get('viewer_width');
      let viewerHeight = model.get('viewer_height');
      const histWidth = model.get('histogram_width');
      
      // Create image canvas
      const imageCanvas = document.createElement('canvas');
      imageCanvas.width = viewerWidth * dpr;
      imageCanvas.height = viewerHeight * dpr;
      imageCanvas.style.width = viewerWidth + 'px';
      imageCanvas.style.height = viewerHeight + 'px';
      imageCanvas.style.background = 'white';
      imageCanvas.style.border = '1px solid #ccc';
      imageCanvas.style.borderRadius = '2px';
      imageCanvas.style.cursor = 'default';
      imageCanvas.tabIndex = 1;  // Make focusable for keyboard events
      imageCanvas.style.outline = 'none';  // Remove default focus outline
      
      const imgCtx = imageCanvas.getContext('2d');
      imgCtx.scale(dpr, dpr);
      
      // Add subtle focus indicator
      imageCanvas.addEventListener('focus', () => {
        imageCanvas.style.boxShadow = '0 0 0 2px rgba(76, 175, 80, 0.5)';
      });
      imageCanvas.addEventListener('blur', () => {
        imageCanvas.style.boxShadow = 'none';
      });
      
      // Create histogram canvas
      const histCanvas = document.createElement('canvas');
      histCanvas.width = histWidth * dpr;
      histCanvas.height = viewerHeight * dpr;
      histCanvas.style.width = histWidth + 'px';
      histCanvas.style.height = viewerHeight + 'px';
      histCanvas.style.background = 'white';
      histCanvas.style.border = '1px solid #ccc';
      histCanvas.style.borderRadius = '2px';
      histCanvas.style.display = model.get('histogram_visible') ? 'block' : 'none';
      
      const histCtx = histCanvas.getContext('2d');
      histCtx.scale(dpr, dpr);
      
      // Create canvas wrapper for image (to hold overlays)
      const canvasWrapper = document.createElement('div');
      canvasWrapper.style.position = 'relative';
      canvasWrapper.style.display = 'inline-block';
      
      canvasWrapper.appendChild(imageCanvas);
      
      // Create scale bar overlay (positioned over image canvas)
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
      scaleBarLabel.textContent = '100 px';
      
      scaleBar.appendChild(scaleBarLine);
      scaleBar.appendChild(scaleBarLabel);
      
      // Create zoom display (positioned over image canvas)
      const zoomDisplay = document.createElement('div');
      zoomDisplay.style.position = 'absolute';
      zoomDisplay.style.top = '10px';
      zoomDisplay.style.left = '10px';
      zoomDisplay.style.padding = '8px 12px';
      zoomDisplay.style.fontSize = '13px';
      zoomDisplay.style.fontFamily = 'monospace';
      zoomDisplay.style.fontWeight = 'bold';
      zoomDisplay.style.background = 'rgba(0, 0, 0, 0.75)';
      zoomDisplay.style.color = 'white';
      zoomDisplay.style.borderRadius = '4px';
      zoomDisplay.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
      zoomDisplay.style.display = model.get('zoom') !== 1.0 ? 'block' : 'none';
      zoomDisplay.style.pointerEvents = 'none';
      zoomDisplay.textContent = `${model.get('zoom').toFixed(2)}x`;
      
      // Add overlays to canvas wrapper
      canvasWrapper.appendChild(scaleBar);
      canvasWrapper.appendChild(zoomDisplay);
      
      // Add canvases to container
      container.appendChild(canvasWrapper);
      container.appendChild(histCanvas);
      
      // Create resize handle (bottom-right corner of entire widget)
      const resizeHandle = document.createElement('div');
      resizeHandle.style.position = 'absolute';
      resizeHandle.style.bottom = '5px';
      resizeHandle.style.right = '5px';
      resizeHandle.style.width = '16px';
      resizeHandle.style.height = '16px';
      resizeHandle.style.cursor = 'nwse-resize';
      resizeHandle.style.background = 'linear-gradient(135deg, transparent 0%, transparent 50%, #888 50%, #888 100%)';
      resizeHandle.style.borderRadius = '0 0 4px 0';
      resizeHandle.style.zIndex = '10';
      resizeHandle.title = 'Drag to resize';
      
      // Create size label
      const sizeLabel = document.createElement('div');
      sizeLabel.style.position = 'absolute';
      sizeLabel.style.bottom = '25px';
      sizeLabel.style.right = '25px';
      sizeLabel.style.padding = '4px 8px';
      sizeLabel.style.background = 'rgba(0, 0, 0, 0.7)';
      sizeLabel.style.color = 'white';
      sizeLabel.style.fontSize = '12px';
      sizeLabel.style.borderRadius = '4px';
      sizeLabel.style.display = 'none';
      sizeLabel.style.pointerEvents = 'none';
      sizeLabel.style.zIndex = '10';
      
      outerContainer.appendChild(container);
      outerContainer.appendChild(resizeHandle);
      outerContainer.appendChild(sizeLabel);
      el.appendChild(outerContainer);
      
      // State variables
      let isResizing = false;
      let isPanning = false;
      let startX, startY, startWidth, startHeight;
      let panStartX, panStartY, panStartCenterX, panStartCenterY;
      let lastPanUpdate = 0;
      
      // Helper functions for scale bar
      function findNiceNumber(target) {
        if (target <= 0) return 1;
        const niceNumbers = [1, 2, 3, 5, 7, 10];
        const magnitude = Math.pow(10, Math.floor(Math.log10(target)));
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
      
      function drawScaleBar() {
        const zoom = model.get('zoom');
        const scale_x = model.get('scale_x');
        const units = model.get('units');
        const windowWidth = model.get('viewer_width');
        const imgWidth = model.get('image_width');
        
        const targetBarWidthPx = windowWidth / 4;
        const usePixels = !scale_x || scale_x <= 0;
        
        if (usePixels) {
          const pixelsPerScreenPixel = imgWidth / windowWidth;
          const targetPixels = targetBarWidthPx * pixelsPerScreenPixel / zoom;
          const niceValue = findNiceNumber(targetPixels);
          const actualBarWidthPx = (niceValue / pixelsPerScreenPixel) * zoom;
          
          scaleBarLine.style.width = actualBarWidthPx + 'px';
          scaleBarLabel.textContent = niceValue + ' px';
        } else {
          const pixelsPerScreenPixel = imgWidth / windowWidth;
          const targetDataPixels = targetBarWidthPx * pixelsPerScreenPixel / zoom;
          const targetPhysicalSize = targetDataPixels * scale_x;
          const niceValue = findNiceNumber(targetPhysicalSize);
          const actualDataPixels = niceValue / scale_x;
          const actualBarWidthPx = (actualDataPixels / pixelsPerScreenPixel) * zoom;
          
          scaleBarLine.style.width = actualBarWidthPx + 'px';
          scaleBarLabel.textContent = formatValue(niceValue) + ' ' + units;
        }
      }
      
      function updateScaleBarPosition() {
        const location = model.get('scalebar_location').toLowerCase();
        
        if (location === 'off') {
          scaleBar.style.display = 'none';
          return;
        }
        
        scaleBar.style.display = 'block';
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
        
        drawScaleBar();
      }
      
      updateScaleBarPosition();
      
      // Resize functionality
      resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = parseInt(imageCanvas.style.width);
        startHeight = parseInt(imageCanvas.style.height);
        sizeLabel.style.display = 'block';
        e.preventDefault();
      });
      
      document.addEventListener('mousemove', (e) => {
        if (isResizing) {
          const deltaX = e.clientX - startX;
          const deltaY = e.clientY - startY;
          
          const rawImageX = model.get('raw_image_size_x');
          const rawImageY = model.get('raw_image_size_y');
          
          let newWidth, newHeight;
          
          if (rawImageX > 0 && rawImageY > 0) {
            const aspectRatio = rawImageX / rawImageY;
            const avgDelta = (deltaX + deltaY) / 2;
            newWidth = Math.max(128, startWidth + avgDelta);
            newHeight = Math.max(128, newWidth / aspectRatio);
            
            if (newHeight < 128) {
              newHeight = 128;
              newWidth = newHeight * aspectRatio;
            }
          } else {
            newWidth = Math.max(128, startWidth + deltaX);
            newHeight = Math.max(128, startHeight + deltaY);
          }
          
          imageCanvas.style.width = newWidth + 'px';
          imageCanvas.style.height = newHeight + 'px';
          imageCanvas.width = newWidth * dpr;
          imageCanvas.height = newHeight * dpr;
          const ctx = imageCanvas.getContext('2d');
          ctx.scale(dpr, dpr);
          
          histCanvas.style.height = newHeight + 'px';
          histCanvas.height = newHeight * dpr;
          const histCtx = histCanvas.getContext('2d');
          histCtx.scale(dpr, dpr);
          
          sizeLabel.textContent = `${Math.round(newWidth)} × ${Math.round(newHeight)}`;
          
          drawImage();
          drawHistogram();
          
          e.preventDefault();
        } else if (isPanning) {
          const rect = imageCanvas.getBoundingClientRect();
          const deltaX = (e.clientX - panStartX) / rect.width;
          const deltaY = (e.clientY - panStartY) / rect.height;
          
          const currentZoom = model.get('zoom');
          const newCenterX = panStartCenterX - deltaX / currentZoom;
          const newCenterY = panStartCenterY - deltaY / currentZoom;
          
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
          
          const finalWidth = Math.round(parseInt(imageCanvas.style.width));
          const finalHeight = Math.round(parseInt(imageCanvas.style.height));
          model.set('viewer_width', finalWidth);
          model.set('viewer_height', finalHeight);
          model.save_changes();
          
          console.log('Resize complete:', finalWidth, 'x', finalHeight);
        }
        if (isPanning) {
          isPanning = false;
          imageCanvas.style.cursor = 'default';
          
          const rect = imageCanvas.getBoundingClientRect();
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
      
      // Mouse wheel zoom
      imageCanvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        const rect = imageCanvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) / rect.width;
        const mouseY = (e.clientY - rect.top) / rect.height;
        
        const currentZoom = model.get('zoom');
        const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = Math.max(0.1, Math.min(100, currentZoom * zoomDelta));
        
        const currentCenterX = model.get('center_x');
        const currentCenterY = model.get('center_y');
        
        const dx = mouseX - 0.5;
        const dy = mouseY - 0.5;
        const zoomRatio = currentZoom / newZoom;
        
        const newCenterX = currentCenterX + dx * (1 - zoomRatio) / newZoom;
        const newCenterY = currentCenterY + dy * (1 - zoomRatio) / newZoom;
        
        model.set('zoom', newZoom);
        model.set('center_x', Math.max(0, Math.min(1, newCenterX)));
        model.set('center_y', Math.max(0, Math.min(1, newCenterY)));
        model.save_changes();
        
        console.log('Zoom:', newZoom.toFixed(2), 'Center:', newCenterX.toFixed(3), newCenterY.toFixed(3));
      });
      
      // Mouse drag to pan
      imageCanvas.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        isPanning = true;
        panStartX = e.clientX;
        panStartY = e.clientY;
        panStartCenterX = model.get('center_x');
        panStartCenterY = model.get('center_y');
        imageCanvas.style.cursor = 'grabbing';
        e.preventDefault();
        // Focus canvas to enable keyboard events
        imageCanvas.focus();
      });
      
      // Focus canvas on mouse enter to ensure keyboard events work
      imageCanvas.addEventListener('mouseenter', () => {
        imageCanvas.focus();
      });
      
      // Keyboard shortcuts - ONLY active when canvas is focused
      imageCanvas.addEventListener('keydown', (e) => {
        if (e.key === 'r' || e.key === 'R') {
          model.set('zoom', 1.0);
          model.set('center_x', 0.5);
          model.set('center_y', 0.5);
          model.save_changes();
          console.log('View reset via keyboard (R key) - canvas focused');
          e.preventDefault();
        } else if (e.key === 'h' || e.key === 'H') {
          const currentVisible = model.get('histogram_visible');
          model.set('histogram_visible', !currentVisible);
          model.save_changes();
          console.log('Histogram visibility toggled (H key):', !currentVisible, '- canvas focused');
          e.preventDefault();
        }
      });
      
      // Draw image function
      function drawImage() {
        const imageBytes = new Uint8Array(model.get('image_bytes').buffer);
        const width = model.get('image_width');
        const height = model.get('image_height');
        const canvasWidth = parseInt(imageCanvas.style.width);
        const canvasHeight = parseInt(imageCanvas.style.height);
        
        if (imageBytes.length === 0) {
          return;
        }
        
        imgCtx.clearRect(0, 0, canvasWidth, canvasHeight);
        
        const imageData = imgCtx.createImageData(width, height);
        const rgba = imageData.data;
        
        for (let i = 0; i < imageBytes.length; i++) {
          const gray = imageBytes[i];
          const idx = i * 4;
          rgba[idx] = gray;
          rgba[idx + 1] = gray;
          rgba[idx + 2] = gray;
          rgba[idx + 3] = 255;
        }
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = width;
        tempCanvas.height = height;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.putImageData(imageData, 0, 0);
        
        imgCtx.drawImage(tempCanvas, 0, 0, width, height, 0, 0, canvasWidth, canvasHeight);
      }
      
      // Draw histogram function
      function drawHistogram() {
        if (!model.get('histogram_visible')) return;
        
        const histData = JSON.parse(model.get('histogram_data'));
        const bins = histData.bins;
        const counts = histData.counts;
        
        const width = parseInt(histCanvas.style.width);
        const height = parseInt(histCanvas.style.height);
        const minVal = model.get('hist_min');
        const maxVal = model.get('hist_max');
        const useLogScale = model.get('log_scale');
        const showColorbar = model.get('show_colorbar');
        const colorbarWidth = model.get('colorbar_width');
        
        histCtx.clearRect(0, 0, width, height);
        
        if (!counts || counts.length === 0) {
          return;
        }
        
        let processedCounts = counts.slice();
        if (useLogScale) {
          processedCounts = counts.map(c => c > 0 ? Math.log10(c + 1) : 0);
        }
        
        const maxCount = Math.max(...processedCounts, 1);
        const chartX = showColorbar ? colorbarWidth + 5 : 0;
        const chartWidth = width - chartX;
        const barHeight = height / counts.length;
        
        histCtx.fillStyle = '#4CAF50';
        histCtx.strokeStyle = '#2E7D32';
        histCtx.lineWidth = 0.5;
        
        for (let i = 0; i < counts.length; i++) {
          const idx = counts.length - 1 - i;
          const barWidth = (processedCounts[idx] / maxCount) * chartWidth;
          const y = i * barHeight;
          
          if (barWidth > 0) {
            histCtx.fillRect(chartX, y, barWidth, barHeight);
            if (barHeight > 2) {
              histCtx.strokeRect(chartX, y, barWidth, barHeight);
            }
          }
        }
        
        if (showColorbar) {
          const gradient = histCtx.createLinearGradient(0, 0, 0, height);
          for (let i = 0; i <= 10; i++) {
            const pos = 1 - i / 10;
            const value = Math.round(pos * 255);
            gradient.addColorStop(i / 10, `rgb(${value}, ${value}, ${value})`);
          }
          histCtx.fillStyle = gradient;
          histCtx.fillRect(0, 0, colorbarWidth, height);
          
          histCtx.strokeStyle = '#666';
          histCtx.lineWidth = 1;
          histCtx.strokeRect(0, 0, colorbarWidth, height);
        }
        
        histCtx.fillStyle = '#666';
        histCtx.font = '10px monospace';
        histCtx.textAlign = 'left';
        histCtx.fillText(maxVal.toFixed(0), chartX + 2, 12);
        histCtx.fillText(minVal.toFixed(0), chartX + 2, height - 3);
      }
      
      // Listen for data changes
      model.on('change:image_bytes', drawImage);
      model.on('change:histogram_data', drawHistogram);
      model.on('change:log_scale', drawHistogram);
      model.on('change:show_colorbar', drawHistogram);
      model.on('change:histogram_visible', () => {
        const visible = model.get('histogram_visible');
        histCanvas.style.display = visible ? 'block' : 'none';
        container.style.gap = visible ? model.get('gap') + 'px' : '0px';
        drawHistogram();
        console.log('Histogram visibility updated:', visible);
      });
      model.on('change:viewer_width', () => {
        const newWidth = model.get('viewer_width');
        imageCanvas.style.width = newWidth + 'px';
        imageCanvas.width = newWidth * dpr;
        const ctx = imageCanvas.getContext('2d');
        ctx.scale(dpr, dpr);
        drawImage();
        drawScaleBar();
      });
      model.on('change:viewer_height', () => {
        const newHeight = model.get('viewer_height');
        imageCanvas.style.height = newHeight + 'px';
        imageCanvas.height = newHeight * dpr;
        histCanvas.style.height = newHeight + 'px';
        histCanvas.height = newHeight * dpr;
        const ctx = imageCanvas.getContext('2d');
        const hCtx = histCanvas.getContext('2d');
        ctx.scale(dpr, dpr);
        hCtx.scale(dpr, dpr);
        drawImage();
        drawHistogram();
      });
      model.on('change:zoom', () => {
        zoomDisplay.textContent = `${model.get('zoom').toFixed(2)}x`;
        zoomDisplay.style.display = model.get('zoom') !== 1.0 ? 'block' : 'none';
        drawScaleBar();
      });
      model.on('change:scalebar_location', updateScaleBarPosition);
      model.on('change:scale_x', drawScaleBar);
      model.on('change:image_width', drawScaleBar);
      model.on('change:units', drawScaleBar);
      
      // Initial draw
      drawImage();
      drawHistogram();
      
      console.log('ResultViewer loaded successfully');
    }
    
    export default { render };
    """

    def __init__(self, result=None, client=None, image=None):
        """Initialize the ResultViewer

        Parameters
        ----------
        result : Result, optional
            A Result object for static display
        client : Client, optional
            A Client instance for dynamic updates
        image : str or FrameType, optional
            Frame type to display when using client (dynamic mode)
        """
        super().__init__()

        # Mode tracking
        self._client = None
        self._image = None
        self._stop_loop = False
        self._last_histogram = None

        if result is not None:
            # Static mode
            self.update_from_result(result)
        elif client is not None and image is not None:
            # Dynamic mode
            from deapi.data_types import FrameType

            self._client = client
            if isinstance(image, str):
                image = FrameType.__getitem__(image.upper())
            self._image = image

            # Set up observers for dynamic updates
            self.observe(self._on_window_size_changed, names=['viewer_width', 'viewer_height'])
            self.observe(self._on_zoom_pan_changed, names=['zoom', 'center_x', 'center_y'])

            # Initial update and start live loop
            self._update_image()
            self._start_auto_update_loop()

    def _on_zoom_pan_changed(self, change):
        """Update image when zoom or pan changes (dynamic mode only)"""
        if self._client is not None:
            self._update_image()

    def _on_window_size_changed(self, change):
        """Update canvas size when window dimensions change (dynamic mode only)"""
        if self._client is not None:
            self._update_image()

    def stop(self):
        """Stop the auto-update loop (for dynamic mode)"""
        self._stop_loop = True

    def _start_auto_update_loop(self):
        """Start a background loop that checks if client is acquiring and updates accordingly"""
        import asyncio

        async def auto_update_loop():
            print("Auto-update loop started - checking acquisition state every 0.5s")
            last_image_hash = None

            while not self._stop_loop:
                try:
                    is_acquiring = self._client.acquiring

                    if is_acquiring:
                        print("Acquisition detected - streaming updates")
                        while self._client.acquiring and not self._stop_loop:
                            img = self._update_image()

                            if img is not None:
                                current_hash = hash(img.tobytes())
                                if current_hash == last_image_hash:
                                    if not self._client.acquiring:
                                        print("Acquisition stopped - returning to poll mode")
                                        break
                                else:
                                    last_image_hash = current_hash

                            await asyncio.sleep(0.033)  # ~30 FPS
                    else:
                        await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error in auto-update loop: {e}")
                    await asyncio.sleep(0.5)

        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(auto_update_loop())
            print("Auto-update loop scheduled in existing event loop")
        except RuntimeError:
            import threading

            def run_async_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(auto_update_loop())

            threading.Thread(target=run_async_loop, daemon=True).start()
            print("Auto-update loop started in new thread with asyncio")

    def get_raw_image_size(self):
        """Get the raw image dimensions from the client"""
        from deapi.data_types import FrameType

        if (FrameType.VIRTUAL_IMAGE0.value <= self._image.value <= FrameType.VIRTUAL_IMAGE4.value or
            FrameType.EXTERNAL_IMAGE1.value <= self._image.value <= FrameType.EXTERNAL_IMAGE4.value):
            self.raw_image_size_x = self._client["Scan - Size X"]
            self.raw_image_size_y = self._client["Scan - Size Y"]
        else:
            self.raw_image_size_x = self._client["Image Size X (pixels)"]
            self.raw_image_size_y = self._client["Image Size Y (pixels)"]

    def get_scale(self):
        """Get scale information from the client"""
        from deapi.data_types import FrameType

        try:
            if (FrameType.VIRTUAL_IMAGE0.value <= self._image.value <= FrameType.VIRTUAL_IMAGE4.value or
                FrameType.EXTERNAL_IMAGE1.value <= self._image.value <= FrameType.EXTERNAL_IMAGE4.value):
                # Diffraction pattern - use mrad units
                self.scale_x = self._client["Diffraction Pixel Size X"]
                self.scale_y = self._client["Diffraction Pixel Size Y"]
                self.units = "mrad" if self.scale_x > 0 else "px"
            else:
                # Real space image - use nm units
                self.scale_x = self._client["Specimen Pixel Size X (nanometers)"]
                self.scale_y = self._client["Specimen Pixel Size Y (nanometers)"]
                self.units = "nm" if self.scale_x > 0 else "px"
        except (KeyError, AttributeError, TypeError) as e:
            print(f"Scale information not available: {e}. Using pixels.")
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.units = "px"

    def _update_image(self):
        """Update the image from the client (dynamic mode)"""
        from deapi import ContrastStretchType
        from deapi.data_types import Attributes, PixelFormat, Histogram

        self.get_raw_image_size()
        self.get_scale()

        if self.raw_image_size_x == -1:
            cx = 0
        else:
            cx = int(self.center_x * self.raw_image_size_x)
            if cx < 1:
                cx = 1
        if self.raw_image_size_y == -1:
            cy = 0
        else:
            cy = int(self.center_y * self.raw_image_size_y)
            if cy < 1:
                cy = 1

        a = Attributes(
            window_width=self.viewer_width,
            window_height=self.viewer_height,
            zoom=self.zoom,
            center_x=cx,
            center_y=cy,
            stretch_type=ContrastStretchType.LINEAR,
        )

        histogram = Histogram(bins=256)
        result = self._client.get_result(self._image, attributes=a, pixel_format=PixelFormat.UINT8, histogram=histogram)

        self._last_histogram = result.histogram

        img = result.image

        if img is None:
            print("No image data received from client.")
            return None

        if img.dtype != np.uint8:
            p_low, p_high = np.percentile(img, [1, 99])
            img_clipped = np.clip(img, p_low, p_high)
            img = ((img_clipped - p_low) / (p_high - p_low) * 255).astype(np.uint8)

        if len(img.shape) == 3:
            if img.shape[2] == 4 or img.shape[2] == 3:
                img = img[:, :, 0]

        if len(img.shape) != 2:
            print(f"Warning: Unexpected image shape {img.shape}")
            return None

        # Update histogram data
        if result.histogram and result.histogram.data:
            histogram = result.histogram
            bins = np.linspace(histogram.min, histogram.max, histogram.bins + 1)
            bin_centers = (bins[:-1] + bins[1:]) / 2

            histogram_json = {
                'bins': bin_centers.tolist(),
                'counts': histogram.data
            }

            hist_min = histogram.min
            hist_max = histogram.max
            hist_bins = histogram.bins
        else:
            counts, edges = np.histogram(img.flatten(), bins=256)
            bin_centers = (edges[:-1] + edges[1:]) / 2

            histogram_json = {
                'bins': bin_centers.tolist(),
                'counts': counts.tolist()
            }

            hist_min = np.nanmin(img)
            hist_max = np.nanmax(img)
            hist_bins = 256

        # Batch all updates
        with self.hold_trait_notifications():
            self.image_width = img.shape[1]
            self.image_height = img.shape[0]
            self.image_bytes = img.tobytes()

            import json
            self.histogram_data = json.dumps(histogram_json)
            self.hist_min = float(hist_min)
            self.hist_max = float(hist_max)
            self.hist_bins = hist_bins

        return img

    def update_from_result(self, result):
        """Update the viewer with a Result object (static mode)

        Parameters
        ----------
        result : Result
            The Result object to display
        """
        import json

        # Convert image to uint8
        image = result.image
        if image.dtype != np.uint8:
            vmin = np.nanmin(image)
            vmax = np.nanmax(image)
            if vmax > vmin:
                image_normalized = ((image - vmin) / (vmax - vmin) * 255).astype(np.uint8)
            else:
                image_normalized = np.zeros_like(image, dtype=np.uint8)
        else:
            image_normalized = image

        # Get histogram data
        if result.histogram and result.histogram.data:
            histogram = result.histogram
            bins = np.linspace(histogram.min, histogram.max, histogram.bins + 1)
            bin_centers = (bins[:-1] + bins[1:]) / 2

            histogram_json = json.dumps({
                'bins': bin_centers.tolist(),
                'counts': histogram.data
            })

            hist_min = histogram.min
            hist_max = histogram.max
            hist_bins = histogram.bins
        else:
            # Compute histogram
            counts, edges = np.histogram(result.image.flatten(), bins=256)
            bin_centers = (edges[:-1] + edges[1:]) / 2

            histogram_json = json.dumps({
                'bins': bin_centers.tolist(),
                'counts': counts.tolist()
            })

            hist_min = np.nanmin(result.image)
            hist_max = np.nanmax(result.image)
            hist_bins = 256

        # Update traits
        with self.hold_trait_notifications():
            self.image_bytes = image_normalized.tobytes()
            self.image_width = image_normalized.shape[1]
            self.image_height = image_normalized.shape[0]
            self.histogram_data = histogram_json
            self.hist_min = float(hist_min)
            self.hist_max = float(hist_max)
            self.hist_bins = hist_bins

            # Set raw image size for aspect ratio maintenance
            self.raw_image_size_x = image_normalized.shape[1]
            self.raw_image_size_y = image_normalized.shape[0]

            # Set viewer dimensions based on image aspect ratio
            aspect_ratio = image_normalized.shape[1] / image_normalized.shape[0]
            if aspect_ratio > 1:
                self.viewer_width = 512
                self.viewer_height = int(512 / aspect_ratio)
            else:
                self.viewer_height = 512
                self.viewer_width = int(512 * aspect_ratio)



