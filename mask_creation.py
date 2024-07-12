import numpy as np
import cv2 as cv
import os
import time
from border_detection import BorderDetector
from skimage.exposure import is_low_contrast


def crop_images():
    img_path = "/home/adele/Downloads/Camera_Trials/Camera_Trials/"
    trial = 8
    tissue = 1

    for j in range(1, 8):
        path = os.path.join(img_path, f"{trial}/{tissue}.BMP")
        print(path)
        img = cv.imread(path)
        # cropped_img = img[1000:2600, 1500:4000]
        cv.namedWindow("test", cv.WINDOW_NORMAL)
        cv.imshow("test", img)
        cv.waitKey(6000)
        # cropped_img = img[1000:2600, 1500:4000]  # crops out the label, alongside black space surrounding tissue
        # cv.imwrite(path, cropped_img)
        tissue += 1


# crop_images()
def main():
    # Create an instance of ImageProcessor
    detector = BorderDetector()

    img_path = "/home/adele/Downloads/Camera_Trials/Camera_Trials/"

    trial = 7
    tissue = 1

    for i in range(1, 6):
        path = os.path.join(img_path, f"{trial}/{tissue}.BMP")
        print(path)
        img = cv.imread(path)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = detector.get_blurred_image(gray, True, 11)
        test = detector.gamma_correction(blur, 1)
        test = cv.convertScaleAbs(test, alpha=1, beta=2)

        #
        if(is_low_contrast(blur, 0.35)):
            print("low")
            # test = cv.convertScaleAbs(gray, alpha=6, beta=8)
            thresh = 40
            test = detector.gamma_correction(blur, 1.5)
            test = cv.convertScaleAbs(test, alpha=1, beta=3)

        else:
            thresh = 90
        #
        # no_white = detector.filter_white_shades(test, 250, 255)
        # clahe = cv.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
        # clahe_img = clahe.apply(no_white)
        #
        blur_two = detector.get_blurred_image(test, True, 15)
        _, thresh = cv.threshold(blur_two, 80, 255, cv.THRESH_BINARY)
        denoised_img = cv.fastNlMeansDenoising(thresh, h=10, templateWindowSize=7, searchWindowSize=21)
        cont = detector.get_image_contours(denoised_img, 4)
        open_img = detector.get_open_image(cont, 10, 4)
        close = detector.get_close_image(open_img, 10, 4)
        conts, _ = cv.findContours(close, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(conts, key=cv.contourArea, reverse=True)[:4]
        result = test.copy()

        for contour in sorted_contours:
            cv.drawContours(result, [contour], -1, (255, 255, 255), 3)

        cv.namedWindow("test", cv.WINDOW_NORMAL)
        cv.imshow("test", result)
        cv.waitKey(5000)
        # cv.imwrite(img_path + f"{trial}/GS/{tissue}.BMP", test)
        tissue += 1

if __name__ == "__main__":
    main()
