"""
histogram_viewer.py

A histogram widget that can link to a SimpleViewer to display live histogram updates.
"""

import anywidget
import numpy as np
import traitlets
from deapi.data_types import Histogram


class HistogramViewer(anywidget.AnyWidget):
    """A histogram viewer widget that can link to a SimpleViewer"""

    # Histogram data as JSON string (bins and counts)
    histogram_data = traitlets.Unicode('{"bins": [], "counts": []}').tag(sync=True)

    # Histogram statistics
    hist_min = traitlets.Float(0.0).tag(sync=True)
    hist_max = traitlets.Float(255.0).tag(sync=True)
    hist_bins = traitlets.Int(256).tag(sync=True)

    # Display settings
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(200).tag(sync=True)
    log_scale = traitlets.Bool(False).tag(sync=True)
    show_stats = traitlets.Bool(True).tag(sync=True)

    # Orientation
    orientation = traitlets.Unicode('horizontal').tag(sync=True)  # 'horizontal' or 'vertical'

    # Colorbar settings
    show_colorbar = traitlets.Bool(True).tag(sync=True)
    colorbar_height = traitlets.Int(20).tag(sync=True)  # Height of colorbar (horizontal) or width (vertical)

    # Link to SimpleViewer (optional)
    _linked_viewer = None
    _viewer_observer = None

    _esm = """
    console.log('HistogramViewer module loading...');
    
    function render({ model, el }) {
      // Create outer container
      const outerContainer = document.createElement('div');
      outerContainer.style.display = 'inline-block';
      outerContainer.style.position = 'relative';
      
      // Create container
      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.flexDirection = 'column';
      container.style.gap = '10px';
      container.style.padding = '10px';
      container.style.background = '#f5f5f5';
      container.style.borderRadius = '4px';
      container.style.position = 'relative';
      
      // Create canvas wrapper for positioning
      const canvasWrapper = document.createElement('div');
      canvasWrapper.style.position = 'relative';
      canvasWrapper.style.display = 'inline-block';
      
      // Create canvas for histogram with high DPI support
      const canvas = document.createElement('canvas');
      const dpr = window.devicePixelRatio || 1;
      const cssWidth = model.get('width');
      const cssHeight = model.get('height');
      
      // Set canvas size for high DPI
      canvas.width = cssWidth * dpr;
      canvas.height = cssHeight * dpr;
      canvas.style.width = cssWidth + 'px';
      canvas.style.height = cssHeight + 'px';
      canvas.style.background = 'white';
      canvas.style.border = '1px solid #ccc';
      canvas.style.borderRadius = '2px';
      
      // Scale context for high DPI
      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      
      canvasWrapper.appendChild(canvas);
      
      // Create controls container
      const controls = document.createElement('div');
      controls.style.display = 'flex';
      controls.style.gap = '15px';
      controls.style.alignItems = 'center';
      controls.style.fontSize = '13px';
      controls.style.flexWrap = 'wrap';
      
      // Stats display (only control shown)
      const statsDiv = document.createElement('div');
      statsDiv.style.marginLeft = 'auto';
      statsDiv.style.fontFamily = 'monospace';
      statsDiv.style.fontSize = '12px';
      statsDiv.textContent = 'Min: 0 | Max: 255 | Bins: 256';
      
      controls.appendChild(statsDiv);
      
      container.appendChild(canvasWrapper);
      container.appendChild(controls);
      
      // Create resize handle (positioned on entire widget)
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
      
      // Create size label (shows during resize)
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
      sizeLabel.textContent = `${cssWidth} × ${cssHeight}`;
      
      outerContainer.appendChild(container);
      outerContainer.appendChild(resizeHandle);
      outerContainer.appendChild(sizeLabel);
      el.appendChild(outerContainer);
      
      // Resize functionality
      let isResizing = false;
      let startX, startY, startWidth, startHeight;
      
      resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = canvas.style.width ? parseInt(canvas.style.width) : cssWidth;
        startHeight = canvas.style.height ? parseInt(canvas.style.height) : cssHeight;
        sizeLabel.style.display = 'block';
        e.preventDefault();
      });
      
      document.addEventListener('mousemove', (e) => {
        if (isResizing) {
          const deltaX = e.clientX - startX;
          const deltaY = e.clientY - startY;
          
          let newWidth = Math.max(200, startWidth + deltaX);
          let newHeight = Math.max(100, startHeight + deltaY);
          
          // Update canvas style size
          canvas.style.width = newWidth + 'px';
          canvas.style.height = newHeight + 'px';
          
          // Update actual canvas size for high DPI
          const dpr = window.devicePixelRatio || 1;
          canvas.width = newWidth * dpr;
          canvas.height = newHeight * dpr;
          
          // Re-scale context
          const ctx = canvas.getContext('2d');
          ctx.scale(dpr, dpr);
          
          sizeLabel.textContent = `${Math.round(newWidth)} × ${Math.round(newHeight)}`;
          
          // Redraw histogram at new size
          drawHistogram();
          
          e.preventDefault();
        }
      });
      
      document.addEventListener('mouseup', (e) => {
        if (isResizing) {
          isResizing = false;
          sizeLabel.style.display = 'none';
          
          // Update model with final size
          const finalWidth = Math.round(parseInt(canvas.style.width));
          const finalHeight = Math.round(parseInt(canvas.style.height));
          model.set('width', finalWidth);
          model.set('height', finalHeight);
          model.save_changes();
          
          console.log('Histogram resize complete:', finalWidth, 'x', finalHeight);
        }
      });
      

      // Draw histogram function
      function drawHistogram() {
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const width = parseInt(canvas.style.width);
        const height = parseInt(canvas.style.height);
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Parse histogram data
        let histData;
        try {
          histData = JSON.parse(model.get('histogram_data'));
        } catch (e) {
          console.error('Failed to parse histogram data:', e);
          return;
        }
        
        const bins = histData.bins;
        const counts = histData.counts;
        
        if (!bins || !counts || bins.length === 0 || counts.length === 0) {
          // Draw empty state
          ctx.fillStyle = '#999';
          ctx.font = '14px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('No histogram data', width / 2, height / 2);
          return;
        }
        
        // Get settings
        const minVal = model.get('hist_min');
        const maxVal = model.get('hist_max');
        const numBins = model.get('hist_bins');
        const useLogScale = model.get('log_scale');
        const orientation = model.get('orientation');
        const showColorbar = model.get('show_colorbar');
        const colorbarSize = model.get('colorbar_height');
        
        // Update stats
        statsDiv.textContent = `Min: ${minVal.toFixed(1)} | Max: ${maxVal.toFixed(1)} | Bins: ${numBins}`;
        
        // Apply log scale if enabled
        let processedCounts = counts.slice();
        if (useLogScale) {
          processedCounts = counts.map(c => c > 0 ? Math.log10(c + 1) : 0);
        }
        
        // Find max count for scaling
        const maxCount = Math.max(...processedCounts, 1);
        
        // Calculate chart area (reserve space for colorbar if enabled)
        let chartX = 0, chartY = 0, chartWidth = width, chartHeight = height;
        const padding = 20;
        
        if (orientation === 'horizontal') {
          chartY = 0;
          chartHeight = showColorbar ? height - colorbarSize - 5 : height - padding;
        } else {
          chartX = showColorbar ? colorbarSize + 5 : 0;
          chartWidth = showColorbar ? width - colorbarSize - 5 - padding : width - padding;
        }
        
        // Draw histogram bars
        ctx.fillStyle = '#4CAF50';
        ctx.strokeStyle = '#2E7D32';
        ctx.lineWidth = 0.5;
        
        if (orientation === 'horizontal') {
          // Horizontal histogram
          const barWidth = chartWidth / counts.length;
          
          for (let i = 0; i < counts.length; i++) {
            const barHeight = (processedCounts[i] / maxCount) * chartHeight;
            const x = i * barWidth;
            const y = chartY + chartHeight - barHeight;
            
            if (barHeight > 0) {
              ctx.fillRect(x, y, barWidth, barHeight);
              if (barWidth > 2) {
                ctx.strokeRect(x, y, barWidth, barHeight);
              }
            }
          }
          
          // Draw axis
          ctx.strokeStyle = '#666';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(0, chartY + chartHeight);
          ctx.lineTo(chartWidth, chartY + chartHeight);
          ctx.stroke();
          
          // Draw scale labels
          ctx.fillStyle = '#666';
          ctx.font = '10px monospace';
          ctx.textAlign = 'left';
          ctx.fillText(minVal.toFixed(0), 2, chartY + chartHeight - 3);
          ctx.textAlign = 'right';
          ctx.fillText(maxVal.toFixed(0), chartWidth - 2, chartY + chartHeight - 3);
          
          // Draw Y-axis max label
          ctx.textAlign = 'left';
          ctx.fillText(useLogScale ? `log(${maxCount.toFixed(0)})` : maxCount.toFixed(0), 2, chartY + 12);
          
          // Draw colorbar if enabled
          if (showColorbar) {
            const colorbarY = chartY + chartHeight + 5;
            const gradient = ctx.createLinearGradient(0, 0, chartWidth, 0);
            
            // Create gradient matching histogram bins (min to max)
            for (let i = 0; i <= 10; i++) {
              const pos = i / 10;
              const value = Math.round(pos * 255);
              const color = `rgb(${value}, ${value}, ${value})`;
              gradient.addColorStop(i / 10, color);
            }
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, colorbarY, chartWidth, colorbarSize);
            
            // Border around colorbar
            ctx.strokeStyle = '#666';
            ctx.lineWidth = 1;
            ctx.strokeRect(0, colorbarY, chartWidth, colorbarSize);
          }
          
        } else {
          // Vertical histogram
          const barHeight = chartHeight / counts.length;
          
          for (let i = 0; i < counts.length; i++) {
            const idx = counts.length - 1 - i;  // Top to bottom: max to min
            const barWidth = (processedCounts[idx] / maxCount) * chartWidth;
            const y = i * barHeight;
            const x = chartX;
            
            if (barWidth > 0) {
              ctx.fillRect(x, y, barWidth, barHeight);
              if (barHeight > 2) {
                ctx.strokeRect(x, y, barWidth, barHeight);
              }
            }
          }
          
          // Draw axis
          ctx.strokeStyle = '#666';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(chartX, 0);
          ctx.lineTo(chartX, chartHeight);
          ctx.stroke();
          
          // Draw scale labels (top = max, bottom = min)
          ctx.fillStyle = '#666';
          ctx.font = '10px monospace';
          ctx.textAlign = 'left';
          ctx.fillText(maxVal.toFixed(0), chartX + 2, 12);
          ctx.fillText(minVal.toFixed(0), chartX + 2, chartHeight - 3);
          
          // Draw X-axis max label
          ctx.textAlign = 'center';
          ctx.fillText(useLogScale ? `log(${maxCount.toFixed(0)})` : maxCount.toFixed(0), chartX + chartWidth / 2, chartHeight - 3);
          
          // Draw colorbar if enabled
          if (showColorbar) {
            const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
            
            // Create gradient matching histogram bins (top = max, bottom = min)
            for (let i = 0; i <= 10; i++) {
              const pos = 1 - i / 10;  // Top is bright (max), bottom is dark (min)
              const value = Math.round(pos * 255);
              const color = `rgb(${value}, ${value}, ${value})`;
              gradient.addColorStop(i / 10, color);
            }
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, colorbarSize, chartHeight);
            
            // Border around colorbar
            ctx.strokeStyle = '#666';
            ctx.lineWidth = 1;
            ctx.strokeRect(0, 0, colorbarSize, chartHeight);
          }
        }
      }
      
      // Listen for histogram data changes
      model.on('change:histogram_data', drawHistogram);
      model.on('change:log_scale', drawHistogram);
      model.on('change:orientation', drawHistogram);
      model.on('change:show_colorbar', drawHistogram);
      model.on('change:colorbar_height', drawHistogram);
      model.on('change:width', () => {
        const newWidth = model.get('width');
        const dpr = window.devicePixelRatio || 1;
        canvas.style.width = newWidth + 'px';
        canvas.width = newWidth * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        drawHistogram();
      });
      model.on('change:height', () => {
        const newHeight = model.get('height');
        const dpr = window.devicePixelRatio || 1;
        canvas.style.height = newHeight + 'px';
        canvas.height = newHeight * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        drawHistogram();
      });
      
      // Initial draw
      drawHistogram();
      
      console.log('HistogramViewer loaded successfully');
    }
    
    export default { render };
    """

    def __init__(self, viewer=None):
        """Initialize the histogram viewer

        Parameters
        ----------
        viewer : SimpleViewer, optional
            A SimpleViewer instance to link to. The histogram will automatically
            update when the viewer's image updates.
        """
        super().__init__()

        if viewer is not None:
            self.link_to_viewer(viewer)

    def link_to_viewer(self, viewer):
        """Link this histogram viewer to a SimpleViewer

        Parameters
        ----------
        viewer : SimpleViewer
            The SimpleViewer instance to link to
        """
        # Unlink from previous viewer if any
        if self._linked_viewer is not None:
            self.unlink_from_viewer()

        self._linked_viewer = viewer

        # Observe the viewer's frame_bytes to detect updates
        self._viewer_observer = viewer.observe(self._on_viewer_update, names=['frame_bytes'])

        # Trigger initial update
        self._on_viewer_update({'new': viewer.frame_bytes})

    def unlink_from_viewer(self):
        """Unlink from the currently linked SimpleViewer"""
        if self._linked_viewer is not None and self._viewer_observer is not None:
            self._linked_viewer.unobserve(self._viewer_observer)
            self._linked_viewer = None
            self._viewer_observer = None

    def _on_viewer_update(self, change):
        """Called when the linked viewer's image updates"""
        if self._linked_viewer is None:
            return

        # Get histogram from the viewer's last result
        if hasattr(self._linked_viewer, '_last_histogram') and self._linked_viewer._last_histogram is not None:
            try:
                histogram = self._linked_viewer._last_histogram

                # Update histogram data
                if histogram and histogram.data:
                    self.update_histogram(histogram)

            except Exception as e:
                print(f"Error updating histogram: {e}")

    def update_histogram(self, histogram):
        """Update the histogram display

        Parameters
        ----------
        histogram : Histogram
            The histogram object containing data to display
        """
        if histogram is None or histogram.data is None:
            return

        # Calculate bin edges
        bins = np.linspace(histogram.min, histogram.max, histogram.bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        # Prepare data for JavaScript
        import json
        histogram_json = json.dumps({
            'bins': bin_centers.tolist(),
            'counts': histogram.data
        })

        # Update traits
        with self.hold_trait_notifications():
            self.histogram_data = histogram_json
            self.hist_min = histogram.min
            self.hist_max = histogram.max
            self.hist_bins = histogram.bins

    def update_from_image(self, image, bins=256):
        """Manually update histogram from an image array

        Parameters
        ----------
        image : numpy.ndarray
            The image to compute histogram from
        bins : int, optional
            Number of histogram bins (default: 256)
        """
        if image is None:
            return

        # Compute histogram
        counts, edges = np.histogram(image.flatten(), bins=bins)
        bin_centers = (edges[:-1] + edges[1:]) / 2

        # Prepare data for JavaScript
        import json
        histogram_json = json.dumps({
            'bins': bin_centers.tolist(),
            'counts': counts.tolist()
        })

        # Update traits
        with self.hold_trait_notifications():
            self.histogram_data = histogram_json
            self.hist_min = float(np.min(image))
            self.hist_max = float(np.max(image))
            self.hist_bins = bins

