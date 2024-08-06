import numpy as np
import cv2 as cv
import os
import time

class BorderDetector:
    def __init__(self):
        pass

    def filter_white_shades(self, img, low, high):

        mask = cv.inRange(img, low, high)
        inv_mask = cv.bitwise_not(mask)
        no_white = cv.bitwise_and(img, img, mask=inv_mask)

        return no_white

    def get_blurred_image(self, img, Guassian=True, shape=5):
        # Blurs image using either the Gaussian blur or regular blur
        if Guassian:
            blur = cv.GaussianBlur(img, (shape, shape), 0)
        else:
            blur = cv.blur(img, (shape, shape))
        return blur

    def get_binary_threshold(self, img, cutoff):

        _, thresh = cv.threshold(img, cutoff, 200, cv.THRESH_BINARY)
        thresh = cv.dilate(thresh, (7, 7), iterations=2)

        return thresh

    def get_canny_edges(self, img):
        # Uses Canny edge detection algorithm to detect edges
        canny = cv.Canny(img, 20, 25, 7)
        dilate = cv.dilate(canny, (10, 10), iterations=20)

        return dilate

    def get_close_image(self, img, shape, num_iterations):
        # Close image to fill holes within tissue
        kernel = np.ones((shape, shape), np.uint8)
        img_close = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel, iterations=num_iterations)

        return img_close

    def get_open_image(self, img, shape, num_iterations):
        # Open image to remove background noise from image
        kernel = np.ones((shape, shape), np.uint8)
        img_close = cv.morphologyEx(img, cv.MORPH_OPEN, kernel, iterations=num_iterations)

        return img_close

    def get_image_contours(self, img, num):
        # Find image contours
        contours, _ = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Sort contours from largest to smallest area
        sorted_contours = sorted(contours, key=cv.contourArea, reverse=True)[:num]

        # Create a blank image to draw all contours
        result = np.zeros(img.shape, dtype=np.uint8)

        # Draw filled contours
        for contour in sorted_contours:
            cv.drawContours(result, [contour], -1, (255, 255, 255), cv.FILLED)

        return result

    def get_cropped_images(self, original_img, contour_imgs):
        cropped_images = []

        # Locate the white pixel regions
        points = np.argwhere(contour_imgs == 255)
        points = np.fliplr(points)  # Row, Col format

        # Get the bounding rectangle around the contour
        x, y, w, h = cv.boundingRect(points)

        # Add buffer of 300 pixels
        x -= 300
        y -= 300
        w += 600
        h += 600

        # Crop the original image based on the bounding rectangle
        cropped_image = original_img[max(0, y):min(original_img.shape[0], y + h),
                        max(0, x):min(original_img.shape[1], x + w)]

        return cropped_image

    def gamma_correction(self, img, gamma):
        # Build a lookup table mapping the pixel values [0, 255] to their adjusted gamma values
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")

        # Apply the gamma correction using the lookup table
        corrected_image = cv.LUT(img, table)

        return corrected_image

# Example of how to use this class
if __name__ == "__main__":
    processor = ImageProcessor()

    # Example usage:
    # img = cv.imread('your_image.jpg', cv.IMREAD_GRAYSCALE)
    # processed_img = processor.filter_white_shades(img)
    # blurred_img = processor.get_blurred_image(processed_img)
    # threshold_img = processor.get_binary_threshold(blurred_img)
    # edges_img = processor.get_canny_edges(threshold_img)
    # closed_img = processor.get_close_image(edges_img, 5, 1)
    # cropped_img = processor.get_cropped_images(img, closed_img)

    # Further processing or saving of cropped_img can be done here

    #
    # tissue_sections = 1  # Number of tissues expected in slide
    # folder_size = 16  # Number of images in folder
    # image_path = "/home/adele/Pictures/BorderDataset/Raw/Gray/"
    # output_dir = "/home/adele/Pictures/BorderDataset/Results_1/"
    #
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # start = time.time()
    # # Iterate through each image
    # for i in range(1, folder_size + 1):
    #     # Load image
    #     print(f"Processing image {i}/{folder_size} ----------------")
    #     image_filename = f"{i}.BMP"
    #     coloured_image = cv.imread(os.path.join(image_path, image_filename))
    #
    #     coloured_image = coloured_image[500:2900, 0:5496]  # Crop glass slide borders
    #
    #     image = cv.cvtColor(coloured_image, cv.COLOR_BGR2GRAY)  # Convert RGB to 8-bit grayscale
    #
    #     white_out_image = filter_white_shades(image)  # Filter out white camera flash regions
    #
    #     gamma_image = gamma_correction(white_out_image, 7.0)  # Gamma correct image - increase brightness
    #
    #     blurred_image = get_blurred_image(gamma_image, False, 3)  # Blur image
    #
    #     threshold_image = get_binary_threshold(blurred_image)  # Binary threshold image
    #
    #     close_image = get_close_image(threshold_image, 4, 10)  # Close gaps in thresholded image
    #
    #     open_image = get_open_image(close_image, 4, 4)  # Eliminate background specs in thresholded image
    #
    #     edges = get_canny_edges(open_image)  # Use Canny algorithm for tight edge detection
    #
    #     contour_image = get_image_contours(edges, tissue_sections)  # Find and fill image contours
    #
    #     open_image = get_open_image(contour_image, 10, 9)  # Close gaps in thresholded image
    #
    #     median = cv.medianBlur(open_image, 15)  # Smooth binary edges
    #
    #     cropped = get_cropped_images(coloured_image, median)
    #
    #     cv.imwrite(f"{output_dir}/{i}_mask.BMP", median)  # Save image
    #
    #     cv.imwrite(f"{output_dir}/{i}.BMP", cropped)
    #
    #     print(f"Done image {i}")
    #
    # end = time.time()
    #
    # print(end - start)
