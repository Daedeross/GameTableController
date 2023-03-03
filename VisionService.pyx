from time import sleep
from BluetoothService import BluetoothService, BleEvent
from picamera2.picamera2 import Picamera2
import cv2
import numpy as np
from perspective_transform import four_point_transform as get_transform

cdef warp_point(M, double x, double y):
    cdef double d = M[2, 0] * x + M[2, 1] * y + M[2, 2]

    return (
        round((M[0, 0] * x + M[0, 1] * y + M[0, 2]) / d), # x
        round((M[1, 0] * x + M[1, 1] * y + M[1, 2]) / d), # y
    )

def default_blob_params():
    params = cv2.SimpleBlobDetector_Params()
    # Change thresholds
    params.minThreshold = 10
    params.maxThreshold = 200

    # Filter by Color (Black<->White)
    params.filterByColor = True
    params.blobColor = 255

    return params

def capture_click(lst):    #assert(len(list = 4))
    #index = 0
    def mouseEvent(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            #list[index] = (x, y)
            lst.append((x, y))
            #index = (index + 1) % 4
    return mouseEvent

class VisionService:

    # _camera = None
    # _blob_params = None
    # _detector = None

    _show_points = False

    _matrix = np.identity(3)
    _inv_matrix = _matrix

    def __init__(self, blob_params: cv2.SimpleBlobDetector_Params = None, camera: Picamera2 = None, size = (800, 600)):
        self.size = size
        if camera:
            self._camera = camera
        else:
            self._camera = Picamera2()
        
        if blob_params:
            self._blob_params = blob_params
        else:
            self._blob_params = default_blob_params()

        self._detector = cv2.SimpleBlobDetector_create(self._blob_params)
        cv2.startWindowThread()
        self._camera.start_preview()
        self._camera.configure(self._camera.create_video_configuration(main={"format": 'XRGB8888', "size": size}))#, transform=libcamera.Transform(hflip=1, vflip=0)))
        self._camera.start()
    
    def in_bounds(self, x, y):
        return x >= 0 and y <= self.size[0] and y >= 0 and y <= self.size[1]

    def get_keypoints(self, image = None):
        if image is None:
            im = self._camera.capture_array()
        else:
            im = image
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        keypoints = self._detector.detect(gray)

        if any(keypoints):
            points = [warp_point(self._matrix, kp.pt[0], kp.pt[1]) for kp in keypoints]
            filtered_points = [(x, y) for (x, y) in points if self.in_bounds(x, y)]
            if (self._show_points):
                for p in filtered_points:
                    im = cv2.circle(im, p, 2, (0, 255, 0), 1)
                im = cv2.rectangle(im, (0,0), self.size, (0,0,255), 1)
                cv2.imshow("Camera", im)
            return filtered_points
        else:
            return []

    def callibrate(self, points):
            
        image: cv2.Mat = self._camera.capture_array()
        for p in points:
            image = cv2.circle(image, p, radius=4, color=(0, 0, 255), thickness=2)

        cv2.imshow("Calibrate", image)
        sleep(2)

        M, size, warped = get_transform(image, np.array(points))
        inv_M = np.linalg.inv(M)
        for p in points:
            warped = cv2.circle(warped, warp_point(M, p[0], p[1]), radius=4, color=(0, 255, 0), thickness=2)
        cv2.imshow("Warped", warped)
        sleep(5)
        self._matrix = M
        self._inv_matrix = inv_M
        self.size = size
        cv2.destroyWindow("Calibrate")
        cv2.destroyWindow("Warped")

    def mouse_callibrate(self):
        self._matrix = np.identity(3)
        self._inv_matrix = np.identity(3)
        points = []
        cv2.namedWindow("Calibrate")
        cv2.setMouseCallback("Calibrate", capture_click(points))
        while len(points) < 4:
            image = self._camera.capture_array()
            for p in points:
                image = cv2.circle(image, p, radius=4, color=(0, 0, 255), thickness=2)

            cv2.imshow("Calibrate", image)
        self.callibrate(points)

    def uart_callibrate(self, ble: BluetoothService):
        self._matrix = np.identity(3)
        self._inv_matrix = np.identity(3)
        points = []
        current_point = None
        # save state to return later
        save_size, save_callback = ble.get_callack()
        save_show_keypoints = self._show_points

        def callback(packet: bytearray):
            nonlocal current_point
            print("{:08b}".format(packet[0]))
            if (packet[0] & BleEvent.ANY_DOWN) and current_point:
                points.append(current_point)
                current_point = None
        
        self._show_points = False
        ble.set_callback(1, callback)
        ble.ensure_ready()
        while len(points) < 4:
            ble.read_uart()
            image = self._camera.capture_array()
            for p in points:
                image = cv2.circle(image, p, radius=4, color=(0, 0, 255), thickness=2)

            keypoints = self.get_keypoints(image)
            if any(keypoints):
                current_point = keypoints[0]
                image = cv2.circle(image, current_point, 4, (0, 255, 0), 2)
            else:
                current_point = None

            cv2.imshow("Calibrate", image)
        
        # restore state
        ble.set_callback(save_size, save_callback)
        self._show_points = save_show_keypoints

        # calibrate with points
        self.callibrate(points)

if __name__ == "__main__":
    service = VisionService()
    ble = BluetoothService()
    service.uart_callibrate(ble)