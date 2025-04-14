from time import sleep
from threading import Thread
import cv2
from picamera2.picamera2 import Picamera2
from libcamera import controls

class CameraService:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    def __init__(self, camera: Picamera2 = None, size = (1024, 768)):
        self.size = size
        if camera:
            self._camera = camera
        else:
            self._camera = Picamera2()
        
        cv2.startWindowThread()
        self._camera.start_preview()
        self._camera.configure(self._camera.create_video_configuration(main={"format": 'XRGB8888', "size": size},
                                                                       controls={"AeExposureMode": controls.AeExposureModeEnum.Short}))
                                                                      #, transform=libcamera.Transform(hflip=1, vflip=0)))
        self._camera.framerate = 30
        self._camera.set_controls({'ExposureTime': 10000})
        self._camera.start()
        self.frame = self._camera.capture_array()
        self.stopped = False

    def start(self):    
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            self.frame = self._camera.capture_array()
            sleep(0.01)
    def stop(self):
        self.stopped = True

def threadVideoGet():
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Main thread shows video frames.
    """

    video_getter = CameraService().start()

    while True:
        if (cv2.waitKey(1) == ord("q")) or video_getter.stopped:
            video_getter.stop()
            break

        frame = video_getter.frame
        # frame = putIterationsPerSec(frame, cps.countsPerSec())
        cv2.imshow("Video", frame)

if __name__ == '__main__':
    threadVideoGet()
