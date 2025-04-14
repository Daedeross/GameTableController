from picamera2.picamera2 import Picamera2
import cv2

def default_blob_params():
    params = cv2.SimpleBlobDetector_Params()
    # Change thresholds
    params.minThreshold = 10
    params.maxThreshold = 200

    # Filter by Color (Black<->White)
    params.filterByColor = True
    params.blobColor = 255

    return params

size = (800, 600)

_camera = Picamera2()

_blob_params = default_blob_params()

_detector = cv2.SimpleBlobDetector_create(_blob_params)
cv2.startWindowThread()
_camera.start_preview()
_camera.configure(_camera.create_video_configuration(main={"format": 'XRGB8888', "size": size}))#, transform=libcamera.Transform(hflip=1, vflip=0)))
_camera.start()

while True:
    image = _camera.capture_array()
    cv2.imshow("TEST", image)
