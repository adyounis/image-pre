import numpy as np
import cv2 as cv
import os
import time
from border_detection import BorderDetector
from skimage.exposure import is_low_contrast
import unittest
from PIL import Image


def calculate_image_resolution(img_path, field_of_view):
    img = Image.open(img_path)
    w, h = img.size
    width_res = (field_of_view[0]/w) * 1000
    height_res = (field_of_view[1]/h) * 1000
    return width_res, height_res


def image_resolution_test(img_path, field_of_view_mm):

    width_res, height_res = calculate_image_resolution(img_path, field_of_view_mm)
    assert width_res < 100, f"Width resolution ({width_res} microns) is not below 100 microns"
    assert height_res < 100, f"Height resolution ({height_res} microns) is not below 100 microns"
    return


class TestVisibleCamera(unittest.TestCase):
    def test_image_resolution(self):
        img_path = "/home/adele/Downloads/lighting_experiments/1.BMP"  # image path
        field_of_view_mm = (85, 55)  # Input format of (HFOV, VFOV)

        try:
            image_resolution_test(img_path, field_of_view_mm)
        except AssertionError as e:
            self.fail(str(e))


if __name__ == "__main__":
    unittest.main()

