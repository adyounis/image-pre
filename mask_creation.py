import numpy as np
import cv2 as cv
import os
import time
from border_detection import BorderDetector
from skimage.exposure import is_low_contrast

class ImageProcessor:
    def __init__(self):
        pass
    def crop_images(self, path):
        """ Will need to fix this up so that it only takes in the current image that the camera took"""
        img = cv.imread(path)
        # cropped_img = img[1000:2600, 1500:4000]
        cv.namedWindow("test", cv.WINDOW_NORMAL)
        cv.imshow("test", img)
        cv.waitKey(6000)
        # cropped_img = img[1000:2600, 1500:4000]  # crops out the label, alongside black space surrounding tissue
        # cv.imwrite(path, cropped_img)

    def edge_detection(self, path):
        detector = BorderDetector()
        img = cv.imread(path)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = detector.get_blurred_image(gray, True, 11)
        test = detector.gamma_correction(blur, 1)
        test = cv.convertScaleAbs(test, alpha=1, beta=2)

        if(is_low_contrast(blur, 0.35)):
            test = detector.gamma_correction(blur, 1.5)
            test = cv.convertScaleAbs(test, alpha=1, beta=3)

        blur_two = detector.get_blurred_image(test, True, 15)
        _, thresh = cv.threshold(blur_two, 40, 255, cv.THRESH_BINARY)
        denoised_img = cv.fastNlMeansDenoising(thresh, h=10, templateWindowSize=7, searchWindowSize=21)
        cont = detector.get_image_contours(denoised_img, 1)
        open_img = detector.get_open_image(cont, 10, 4)
        close = detector.get_close_image(open_img, 10, 4)
        conts, _ = cv.findContours(close, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(conts, key=cv.contourArea, reverse=True)[:1]
        result = img.copy()

        for contour in sorted_contours:
            cv.drawContours(result, [contour], -1, (0, 0, 255), 5)
            pixel_area = cv.contourArea(contour)
            mm_per_pixel = 0.015  # TODO: adjust once real values come in (currently estimated to be 15 um)
            mm_area = pixel_area*(mm_per_pixel ** 2)
        return result, mm_area

