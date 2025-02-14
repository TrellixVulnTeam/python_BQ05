#pylint: skip-file
'''classify stuff'''
import argparse as ap

from skimage.transform import pyramid_gaussian
from skimage.io import imread
from skimage.feature import hog
from sklearn.externals import joblib
import cv2

from opencvlib.roi import nms_rects
from config import cells_per_block, min_wdw_sz, model_path, normalize, orientations, \
    pixels_per_cell, step_size, threshold, visualize
from opencvlib.winpyr import slide_win_abs

if __name__ == "__main__":
    # Parse the command line arguments
    parser = ap.ArgumentParser()
    parser.add_argument(
        '-i', "--image", help="Path to the test image", required=True)
    parser.add_argument('-d', '--downscale', help="Downscale ratio", default=1.25,
                        type=int)
    parser.add_argument('-v', '--visualize', help="Visualize the sliding window",
                        action="store_true")
    args = vars(parser.parse_args())

    # Read the image
    im = imread(args["image"], as_grey=False)
    min_wdw_sz = (100, 40)
    step_size = (10, 10)
    downscale = args['downscale']
    visualize_det = args['visualize']

    # Load the classifier
    clf = joblib.load(model_path)

    # List to store the detections
    detections = []
    # The current scale of the image
    scale = 0
    # Downscale the image and iterate
    for im_scaled in pyramid_gaussian(im, downscale=downscale):
        # This list contains detections at the current scale
        cd = []
        # If the width or height of the scaled image is less than
        # the width or height of the window, then end the iterations.
        if im_scaled.shape[0] < min_wdw_sz[1] or im_scaled.shape[1] < min_wdw_sz[0]:
            break
        for (x, y, im_window) in slide_win_abs(im_scaled, min_wdw_sz, step_size):
            if im_window.shape[0] != min_wdw_sz[1] or im_window.shape[1] != min_wdw_sz[0]:
                continue
            # Calculate the HOG features
            fd = hog(im_window, orientations, pixels_per_cell,
                     cells_per_block, visualize, normalize)
            pred = clf.predict(fd)
            if pred == 1:
                print("Detection:: Location -> ({}, {})".format(x, y))
                print("Scale ->  {} | Confidence Score {} \n".format(scale,
                                                                     clf.decision_function(fd)))
                detections.append((x, y, clf.decision_function(fd),
                                   int(min_wdw_sz[0] * (downscale**scale)),
                                   int(min_wdw_sz[1] * (downscale**scale))))
                cd.append(detections[-1])
            # If visualize is set to true, display the working
            # of the sliding window
            if visualize_det:
                clone = im_scaled.copy()
                for x1, y1, _, _, _ in cd:
                    # Draw the detections at this scale
                    cv2.rectangle(clone, (x1, y1), (x1 + im_window.shape[1], y1 +
                                                    im_window.shape[0]), (0, 0, 0), thickness=2)
                cv2.rectangle(clone, (x, y), (x + im_window.shape[1], y +
                                              im_window.shape[0]), (255, 255, 255), thickness=2)
                cv2.imshow("Sliding Window in Progress", clone)
                cv2.waitKey(30)
        # Move the the next scale
        scale += 1

    # Display the results before performing NMS
    clone = im.copy()
    for (x_tl, y_tl, _, w, h) in detections:
        # Draw the detections
        cv2.rectangle(im, (x_tl, y_tl), (x_tl + w, y_tl + h),
                      (0, 0, 0), thickness=2)
    cv2.imshow("Raw Detections before NMS", im)
    cv2.waitKey()

    # Perform Non Maxima Suppression
    detections = nms_rects(detections, threshold)

    # Display the results after performing NMS
    for (x_tl, y_tl, _, w, h) in detections:
        # Draw the detections
        cv2.rectangle(clone, (x_tl, y_tl), (x_tl + w, y_tl + h),
                      (0, 0, 0), thickness=2)
    cv2.imshow("Final Detections after applying NMS", clone)
    cv2.waitKey()
