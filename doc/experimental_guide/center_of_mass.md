Weighted Centroid (Center of Mass)
==================================

The weighted centroid, also known as the center of mass, is a point that represents the average position of a set
of points, weighted by their respective "masses" or in 4D STEM experiments the values of the pixels.  In 4D STEM, 
this technique is highly useful as it measures the shift in the electron beam due to the electric and magnetic field.

This gives phase contrast similar to what is observed using differential phase contrast (DPC) imaging using segmented
detectors. The weighted centroid, however, gives a more quantitative measure of the shift in the beam and can be used 
for quantitative measurements of the electric and magnetic fields in the sample.


Experimental Setup
------------------

| Mode / Use Case                         | Convergence Angle (mrad) | Detector Readout    | Electrons per Pixel | Mode        |
|-----------------------------------------|--------------------------|---------------------|---------------------|-------------|
| High-Resolution STEM                    | 20–30                    | 128x128 - 256x256   | 5–20                | Integrating |
| Atomic Column Imaging                   | 20–40                    | 128x128 - 256x256   | 20–100              | Integrating |
| Low-Dose Phase Imaging (Beam Sensitive) | 10–20                    | 256x256-  512x512   | 20–100              | Counting    |
| Magnetic/Electric Field Mapping         | 10–20                    | 256x256 - 1024x1024 | 40–1000             | Integrating |


You can see that there are a large range of experimental parameters that can be used to collect 4D STEM data for weighted centroid analysis.
For more accurate results it is important to use a large number of pixels on the detector to accurately measure the 
small shifts in the beam.  These are typically on the order of a fraction of a pixel to a few pixels. The camera length
should be adjusted so that the zero beam is large enough to fill about half to 2/3 of the detector to give good 
sensitivity to small shifts in the beam. Figure 1 shows a good size zero beam.

.. image:: /_static/experimental_guide/center_of_mass/center_of_mass_zero_beam.png
   :alt: Center of Mass Setup
   :width: 600px
   :align: center

   Figure 1: Example of a good size zero beam for weighted centroid analysis.


Mission Control
---------------

1. Set up the microscope for 4D STEM data collection. This typically involves setting the microscope to
   scanning mode, setting the convergence angle, camera length so that the zero beam is looks like Figure 1, 
   on the detector.
2. (Optional) Open the 4D STEM Tab in Mission Control and use the Vacuum Reference Tab to take a vacuum reference
   dataset. This is just a simple raster scan which finds the weighted centroid of the zero beam as it scans across
   the sample.  This will be used to "center" the zero beam to the exact center of the detector. The resultant
   diffraction patterns will be aligned to the nearest pixel. The residuals will also be saved and will be applied
   to any subsequent centroid calculations. 
3. Create a Virtual Image using the Centroid and a Circular Mask. In this case the mask should be set to cover the entire
   zero beam.  The Virtual Image will show the shift in the beam as it scans across the sample. In cases where the 
   sample is thick there might be some structure in the zero beam.  In this case it might be better to use a mask that
   only covers the edge of the zero beam.  This is less dose efficient but can be very effective in reducing 
   the effects of Kikuchi diffraction.
4. Start a 4D STEM acquisition using the 4D STEM Tab in Mission Control.  The Virtual Image will update
   in real time as the data is collected. For weighted centroid analysis it is best to save all the virtual images. 
   The weighted centroid virtual image will be saved as [[[Com X1, Com Y1],[Com X2, Com Y2]...],].  The units are in 
   pixels from the center of the diffraction pattern. In the case where a vacuum reference was taken the
   residuals will be applied to the data.
5. After (or during) the acquisition you can use the "Image Display" tab in Mission Control to adjust the "virtual 
   image visualization option".  This allows you to switch between displaying the X component, Y component, the 
   magnitude, the angle or the angle + the magnitude expressed as the hue and the brightness respectively.  This can 
   be very useful for visualizing the data. These values differ slightly from the values saved in the virtual image. 
   Figure 3 shows a decision tree for determining the reference point for the weighted centroid vector and the rotation
   from the Advanced Property `Centroid Angle Offset`.

.. image:: /_static/experimental_guide/center_of_mass/circular_masks_example.JPG
   :alt: Example of a mask for weighted centroid analysis
   :width: 600px
   :align: center

   Figure 2: Two examples of circular masks for weighted centroid analysis.


.. image:: /_static/experimental_guide/center_of_mass/centroid_reference_decision_tree.png
   :alt: Decision Tree for Weighted Centroid Analysis reference point
   :width: 600px
   :align: center

   Figure 3: The work flow for determining the origin of the weighted centroid vector in Mission Control for display.
