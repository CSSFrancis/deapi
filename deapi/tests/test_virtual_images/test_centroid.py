import time

import pytest
import hyperspy.api as hs
import numpy as np
import matplotlib.pyplot as plt

from deapi.data_types import Attributes, VirtualVisualizationOption, ContrastStretchType


class TestCentroid:

    @pytest.fixture(autouse=True)
    def clean_state(self, client):
        # First set the hardware ROI to a known state
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        client["Hardware Binning X"] = 1
        client["Hardware Binning Y"] = 1
        client["Scan - Type"] = "Raster"
        # Set the software Binning to 1
        client["Binning X"] = 1
        client["Binning Y"] = 1
        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        previous_pattern = client["Test Pattern"]
        client["Test Pattern"] = "PNJunction-Scan"
        client["Simulator Add Descan to Scan"] = "Off"

        client.virtual_masks[0].calculation = "Centroid"
        from skimage.draw import disk
        rr,cc = disk(center=(128, 128),
             radius=100,
             shape=client.virtual_masks[0][:].shape)
        client.virtual_masks[0][:] = 1
        client.virtual_masks[0][rr, cc] = 2




    def teardown(self):
        time.sleep(0.1)

    @pytest.mark.server
    def test_rotate(self, client):
        x_centroids = []
        y_centroids = []
        for ang in [0, 90, 180]:
            size_x = 16
            size_y = 16
            client.scan(size_x= size_x, size_y=size_y, enable=True)
            client["Frames Per Second"] = 500
            client["Centroid Angle Offset"] = ang
            client.start_acquisition(1)
            client.wait_until_finished()
            cenx, _, _, _ = client.get_result("virtual_image1",
                           attributes=dict(virtual_visualization_option=VirtualVisualizationOption.CENTROID_X,
                           stretch_type=ContrastStretchType.NONE),
                                             pixel_format="FLOAT32")
            ceny, _, _, _ = client.get_result("virtual_image1",
                           attributes=dict(virtual_visualization_option=VirtualVisualizationOption.CENTROID_Y,
                           stretch_type=ContrastStretchType.NONE),
                                             pixel_format="FLOAT32")
            x_centroids.append(cenx)
            y_centroids.append(ceny)
        # rotated 180 degrees should be negative y
        np.testing.assert_allclose(x_centroids[0], -x_centroids[2], atol=0.01)
        np.testing.assert_allclose(y_centroids[0], -y_centroids[2], atol=0.01)

        # rotated 90 degrees should swap x and y
        np.testing.assert_allclose(x_centroids[0], -y_centroids[1], atol=0.01)
        np.testing.assert_allclose(y_centroids[0], x_centroids[1], atol=0.01)

    @pytest.mark.server
    def test_angle_up_sample(self, client):
        client.virtual_masks[0].calculation = "Centroid"
        #client["Centroid Angle Offset"] =3.141592 # 180 degrees in radians

        from skimage.draw import disk
        rr,cc = disk(center=(128, 128),
             radius=100,
             shape=client.virtual_masks[0][:].shape)
        client.virtual_masks[0][:] = 1
        client.virtual_masks[0][rr, cc] = 2

        size_x = 128*2
        size_y = 128*2
        client.scan(size_x= size_x, size_y=size_y, enable=True)
        client["Frames Per Second"] = 500
        client["Scan - Vacuum Reference Correction"] = "Off"
        client.start_acquisition(1)
        client.wait_until_finished()


        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.ANGLE,
                          stretch_type=ContrastStretchType.NONE)
        angle, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")
        attr = Attributes(frame_width=size_x//2,
                          frame_height=size_y//2,
                          window_height=size_x//2,
                          window_width=size_y//2,
                          virtual_visualization_option=VirtualVisualizationOption.ANGLE,
                          stretch_type=ContrastStretchType.NONE)
        angle2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y//2,
                          window_height=size_y//2,
                          window_width=size_x,
                          virtual_visualization_option=VirtualVisualizationOption.NONE,
                          stretch_type=ContrastStretchType.NONE)
        raw, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        fig, axs = plt.subplots(1, 2)
        print("Min/Max: ",np.max(raw), np.min(raw))
        axs[0].imshow(raw[70:80, 140:160:2])
        axs[0].set_title(f"COMX")
        axs[1].set_title("COMY")
        axs[1].imshow(raw[70:80, 141:161:2])

        fig, axs = plt.subplots(1, 2)
        axs[0].imshow(angle2[70:80,70:80])
        axs[1].imshow(angle[140:160,140:160])
        plt.show()

        # Make sure that the entire region is a similar angle.
        np.testing.assert_allclose(angle2[70:80,70:80], angle2[75,75], atol=0.1)


    @pytest.mark.server
    def test_angle_amplitude(self, client):
        client.virtual_masks[0].calculation = "Centroid"
        #client["Centroid Angle Offset"] =3.141592 # 180 degrees in radians

        from skimage.draw import disk
        rr,cc = disk(center=(128, 128),
             radius=100,
             shape=client.virtual_masks[0][:].shape)
        client.virtual_masks[0][:] = 1
        client.virtual_masks[0][rr, cc] = 2

        size_x = 128
        size_y = 128
        client.scan(size_x= size_x, size_y=size_y, enable=True)
        client["Frames Per Second"] = 500
        client["Scan - Vacuum Reference Correction"] = "Off"
        client.start_acquisition(1)
        client.wait_until_finished()
        attr = Attributes(window_height=size_x,
                          window_width=size_y*3,
                          virtual_visualization_option=VirtualVisualizationOption.AMPLITUDE_ANGLE,
                          stretch_type=ContrastStretchType.LINEAR)
        image, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="UINT8")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.AMPLITUDE,
                          stretch_type=ContrastStretchType.NONE)
        amp, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.ANGLE,
                          stretch_type=ContrastStretchType.NONE)
        angle, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x*2,
                          frame_height=size_y,
                          window_height=size_y,
                          window_width=size_x*2,
                          virtual_visualization_option=VirtualVisualizationOption.NONE,
                          stretch_type=ContrastStretchType.NONE)
        raw, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.CENTROID_X,
                          stretch_type=ContrastStretchType.NONE)
        comx, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.CENTROID_Y,
                          stretch_type=ContrastStretchType.NONE)
        comy, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        assert image.shape == (size_x,size_y*3)
        fig, axs = plt.subplots(1, 2)
        print("Min/Max: ",np.max(raw), np.min(raw))
        axs[0].imshow(raw[:, ::2])
        axs[0].set_title(f"COMX")
        axs[1].set_title("COMY")
        axs[1].imshow(raw[:, 1::2])

        plt.show()
        #np.testing.assert_allclose(image[:,1::3], 1
        assert image.shape == (size_x,size_y*3)

        #np.testing.assert_allclose(raw[:, ::2], comx, atol=0.1)
        #np.testing.assert_allclose(raw[:, 1::2], comy, atol=0.1)

        assert image.shape == (size_x,size_y*3)
        fig, axs = plt.subplots(1, 2)
        print("Min/Max: ",np.max(raw), np.min(raw))
        axs[0].imshow(comx)
        axs[0].set_title(f"COMX")
        axs[1].set_title("COMY")
        axs[1].imshow(comy)
        plt.show()
        #np.testing.assert_allclose(image[:,1::3], 1
        assert image.shape == (size_x,size_y*3)


        fig, axs = plt.subplots(1, 3)
        axs[0].imshow(amp)
        axs[0].set_title("Amplitude")
        axs[1].set_title("Angle")
        axs[2].set_title("Amplitude and Angle")
        axs[1].imshow(angle)

        axs[2].imshow(image.reshape((size_x,size_y,3)))
        plt.show()
        #np.testing.assert_allclose(image[:,1::3], 1)

        size_x = 128
        size_y = 128
        client.scan(size_x= size_x, size_y=size_y, enable=True)
        client["Frames Per Second"] = 500
        client["Scan - Vacuum Reference Correction"] = "Off"
        client.start_acquisition(1)
        client.wait_until_finished()
        attr = Attributes(frame_width=size_x*3,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y*3,
                          virtual_visualization_option=VirtualVisualizationOption.AMPLITUDE_ANGLE,
                          stretch_type=ContrastStretchType.LINEAR)
        image2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="UINT8")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.AMPLITUDE,
                          stretch_type=ContrastStretchType.NONE)
        amp2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.ANGLE,
                          stretch_type=ContrastStretchType.NONE)
        angle2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x*2,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y*2,
                          virtual_visualization_option=VirtualVisualizationOption.NONE,
                          stretch_type=ContrastStretchType.NONE)
        raw2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.CENTROID_X,
                          stretch_type=ContrastStretchType.NONE)
        comx2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")

        attr = Attributes(frame_width=size_x,
                          frame_height=size_y,
                          window_height=size_x,
                          window_width=size_y,
                          virtual_visualization_option=VirtualVisualizationOption.CENTROID_Y,
                          stretch_type=ContrastStretchType.NONE)
        comy2, pixel_format, attributes, histogram  =  client.get_result("virtual_image1",
                                                                         attributes=attr,
                                                                         pixel_format="FLOAT32")
        #np.testing.assert_allclose(image, image2)
        np.testing.assert_allclose(amp, amp2)
        np.testing.assert_allclose(angle, angle2)
        np.testing.assert_allclose(raw, raw2)
        np.testing.assert_allclose(comx, comx2)
        np.testing.assert_allclose(comy, comy2)

    @pytest.mark.server
    def test_change_virtual_image(self, client):

        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        client["Test Pattern"] = "SW Constant 1"

        client.virtual_masks[0].calculation = "Sum"
        client.scan(size_x= 16, size_y=16, enable=True)
        client.wait_until_finished()
        mask = client.virtual_masks[0][:]
        client.virtual_masks[0].calculation = "Centroid"
        client.scan(size_x= 16, size_y=16, enable=True)
        client.wait_until_finished()
        client.get_result("virtual_image1")
        client.virtual_masks[0].calculation = "Sum"
        mask = client.virtual_masks[0][:]
        client.scan(size_x= 16, size_y=16, enable=True)
        client.wait_until_finished()
        client.get_result("virtual_image1")


    @pytest.mark.server
    def test_vacuum_reference(self, client):

        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        client["Test Pattern"] = "SW Constant 1"

        client.scan(size_x= 16, size_y=16, enable=True)
        client.take_vacuum_reference()

        reference = client["Reference - Vacuum"]

        assert "Applied" in reference
        reference_file= reference.split("(")[1].split(")")[0]
        reference = hs.load(reference_file)
        assert reference.data.shape == (16, 32)
        # This should be zero shifts for an image that is centered (like a constant image of 1s)
        np.testing.assert_array_almost_equal(reference.data, 0)

    @pytest.mark.server
    def test_vacuum_reference_descan(self, client):

        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        previous_pattern = client["Test Pattern"]
        client["Test Pattern"] = "Strain-Scan"
        client["Simulator Add Descan to Scan"] = "On"

        client.scan(size_x= 16, size_y=16, enable=True)
        client.take_vacuum_reference()
        client.wait_until_finished()
        reference = client["Reference - Vacuum"]

        assert "Applied" in reference or "Valid" in reference
        reference_file= reference.split("(")[1].split(")")[0]
        reference = hs.load(reference_file)
        assert reference.data.shape == (16, 32)
        # This should not be zero shifts and increasing shifts in the x/y direction

        x_shift = reference.data[0,::2]
        y_shift = reference.data[:,::2][:,0]
        assert np.all(np.diff(x_shift) > 0.1)
        assert np.all(np.diff(y_shift) > 0.1)
        client["Simulator Add Descan to Scan"] = "Off"
        client["Test Pattern"] = previous_pattern


    @pytest.mark.server
    def test_com_constant(self, client):

        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        client["Test Pattern"] = "SW Constant 1"

        client.virtual_masks[0].calculation = "Centroid"
        client.virtual_masks[0][:] = 2 # Set to all 2s to get the centroid of the whole image

        client.scan(size_x= 16, size_y=16, enable=True)
        client.start_acquisition(1)
        while client.acquiring:
            time.sleep(0.1)

        image, pixel_format, attributes, histogram  =  client.get_result("virtual_image1")
        #assert image.shape == (16, 32) # requires the number of vectors per virtual image be a property
        np.testing.assert_allclose(image, 0)

    @pytest.mark.server
    def test_vacuum_reference_centroid(self, client):
        """ The centroid should make the zero beam completely centered...
        """

        client["Hardware ROI Size X"] = 256
        client["Hardware ROI Size Y"] = 256
        client["Hardware ROI Offset X"] = client["Hardware Frame Size X"] // 2 - 128
        client["Hardware ROI Offset Y"] = client["Hardware Frame Size Y"] // 2 - 128
        previous_pattern = client["Test Pattern"]
        client["Test Pattern"] = "Strain-Scan"
        client["Simulator Add Descan to Scan"] = "On"

        client.scan(size_x= 16, size_y=16, enable=True)
        client.take_vacuum_reference()
        client.wait_until_finished()

        client["Scan - Vacuum Reference Correction"] = "On"

        client.virtual_masks[0].calculation = "Centroid"
        client.virtual_masks[0][:] = 1
        client.virtual_masks[0][128-20:128+20,128-20:128+20] = 2  # Only the center 64x64 pixels


        client.start_acquisition(1)
        client.wait_until_finished()

        image, pixel_format, attributes, histogram  =  client.get_result("virtual_image1", pixel_format= "FLOAT32")
        #assert image.shape == (16, 32) # requires the number of vectors per virtual image be a property
        np.testing.assert_allclose(image, 0, atol=.2)


        client["Scan - Vacuum Reference Correction"] = "Off"

        client.virtual_masks[0].calculation = "Centroid"
        client.virtual_masks[0][:] = 1
        client.virtual_masks[0][128-24:128+24,128-24:128+24] = 2  # Only the center 64x64 pixels

        assert client.virtual_masks[0][:].sum() > 0

        client.start_acquisition(1)
        client.wait_until_finished()

        image, pixel_format, attributes, histogram  =  client.get_result("virtual_image1", pixel_format= "FLOAT32")
