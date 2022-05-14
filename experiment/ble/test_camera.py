from cv2 import blur
from pkg_resources import find_distributions
from picamera2.picamera2 import Picamera2
import cv2
import numpy as np

desired_size = (520, 400)

params = cv2.SimpleBlobDetector_Params()

# Change thresholds
params.minThreshold = 10
params.maxThreshold = 200

# Filter by Area.
# params.filterByArea = True
# params.minArea = 1500

# # Filter by Circularity
# params.filterByCircularity = True
# params.minCircularity = 0.1

# # Filter by Convexity
# params.filterByConvexity = True
# params.minConvexity = 0.87

# # Filter by Inertia
# params.filterByInertia = True
# params.minInertiaRatio = 0.01

# Filter by Color (Black<->White)
params.filterByColor = True
params.blobColor = 255

detector = cv2.SimpleBlobDetector_create(params)

arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
arucoParams = cv2.aruco.DetectorParameters_create()
arucoParams.minMarkerPerimeterRate = 0.01

cv2.startWindowThread()

picam2 = Picamera2()
picam2.start_preview()
picam2.configure(picam2.preview_configuration(main={"format": 'XRGB8888', "size": (1024, 768)}))
picam2.start()

def apply_brightness_contrast(input_img, brightness = 0, contrast = 0):
    
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    
    if contrast != 0:
        f = 131*(contrast + 127)/(127*(131-contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf


def find_keypoints():
    while True:
        im = picam2.capture_array()

        grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        keypoints = detector.detect(grey)
        # print(len(keypoints))
        im_with_keypoints = cv2.drawKeypoints(grey, keypoints, np.array([]), (0,255,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        cv2.imshow("Camera", im_with_keypoints)

def find_edges():
    while True:
        image = picam2.capture_array()
        ratio = image.shape[0] / desired_size[0]
        resized = cv2.resize(image, desired_size)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = apply_brightness_contrast(gray, 64, 64)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 25, 100)

        cv2.imshow("Image", gray)
        cv2.imshow("Edged", edged)

kernel = np.array([[0, -1, 0],
                   [-1, 5,-1],
                   [0, -1, 0]])

def find_fiducials():
    while True:
        image = picam2.capture_array()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #gray = apply_brightness_contrast(gray, 64, 99)
        #blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        #gray = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
        #gray = cv2.filter2D(src=gray, ddepth=-1, kernel=kernel)
        (corners, ids, rejected) = cv2.aruco.detectMarkers(gray, arucoDict, parameters=arucoParams)
        if len(corners) > 0:
            gray = cv2.aruco.drawDetectedMarkers(gray, corners, ids)
        cv2.imshow("Image", gray)

if __name__ == '__main__':
    find_edges()