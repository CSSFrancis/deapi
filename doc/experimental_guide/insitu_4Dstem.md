In Situ 4D-STEM (5D STEM)
=========================

In situ 4D-STEM, also known as 5D STEM, is an advanced microscopy technique where multiple 4D STEM experiments
are collected sequentially. This results in a five-dimensional dataset (1D Temporal + 2D spatial + 2D diffraction). 
This technique is particularly useful for studying dynamic processes in materials, such as phase transitions,
chemical reactions, or other time-dependent phenomena at the nanoscale.  Often times these experiments are
combined with in situ holders that allow for the application of stimuli such as heating, cooling, electrical
biasing, or mechanical stress.

Experimental Setup
------------------
The experimental setup for in situ 4D-STEM is similar to standard 4D-STEM.  In this case you will want to consider
the temporal resolution needed to capture the dynamic process, the total dose that the sample can withstand, the 
spatial resolution needed to resolve the features of interest, and the size of the field of view.  Often times 
there are distinct trade-offs between these parameters.

It's worth discussing how the detector design and readout mode is important to consider.  Most of the DE detectors
read row by row. This means that the readout time is proportional to the number of rows.  This means that to maximize
the total dose on the detector (for a square read out) you want to use the entire detector area.  

The Celeritas has a unique architecture in that it is designed to 


| Mode / Use Case                         | Convergence Angle (mrad) | Detector Readout    | Mode        |
|-----------------------------------------|--------------------------|---------------------|-------------|
| In situ Ptychography                    | 20–30                    | 64x64 - 128-128     | Integrating |
| Low-Dose Phase Imaging (Beam Sensitive) | .5-20                    | 256x256             | Counting    |
| Magnetic/Electric Field Mapping         | 10–20                    | 256x256 - 1024x1024 | Integrating |

