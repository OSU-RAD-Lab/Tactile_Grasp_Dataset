# code modified from OpenCv's Documentation: https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
import cv2 as cv
import threading
import time
import pathlib
import matplotlib.pyplot as plt

class Camera():
    def __init__(self, camera_name, port_num):
        self.camera_name = camera_name.replace(" ", "_")

        self.port_num = port_num
        self.cap = cv.VideoCapture(self.port_num)

        target_fps = 12.0
        self.cap.set(cv.CAP_PROP_FPS, target_fps)
        self.cap_fps = target_fps #self.cap.get(cv.CAP_PROP_FPS)
        self.inter_frame_period = 1/self.cap_fps

        target_width = 640
        target_height = 480
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, target_width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, target_height)
        width = int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.cap_dim = (width, height)

        # The following code gives warnings and slows down the camera, just leave the defaults
        #self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG'))
        #self.cap.set(cv.CAP_PROP_BUFFERSIZE, 1)

        # Define the codec and create VideoWriter object
        self.fourcc = cv.VideoWriter_fourcc(*'mp4v')

        self.recording = False
        self.calibrated = False
        self.video_writer = None
        self.last_frame = None
        self.recording_thread = None


    def create_video_writer(self, path):
        video_file_path = path / f"{self.camera_name}_video.mp4"
        if(self.video_writer is not None):
            self.video_writer.release()
            self.video_writer = None
        self.video_writer = cv.VideoWriter(str(video_file_path), self.fourcc, self.cap_fps, self.cap_dim)
        return(self.video_writer)


    def calibrate(self):
            print(f"[{self.camera_name}] Calibrating camera...")
            # give some time to boot up
            time.sleep(3)
            # ensure there is a starting frame before recording
            self.get_next_frame()
            self.calibrated = True
            print(f"[{self.camera_name}] Camera calibrated")


    def start(self):
            print(f"[{self.camera_name}] Starting camera...")
            # check to ensure the camera isnt already started
            if(self.is_recording()):
                print(f"[{self.camera_name}] Camera already started")
                return
            # check to make sure the camera is calibrated
            if(not self.is_calibrated()):
                print(f"[{self.camera_name}] Camera not calibrated...")
                self.calibrate()
            # enable the camera and start the recording thread
            self.enable_recording()
            self.recording_thread = threading.Thread(target=self.record, args=())
            self.recording_thread.start()


    def stop(self):
        with threading.Lock():
            self.disable_recording()


    def read(self):
        return(self.last_frame)


    def record(self):
        print(f"[{self.camera_name}] Recording started @ {self.cap_fps} FPS")
        while(self.is_recording() and self.is_active()):
            self.get_next_frame()


    def get_next_frame(self):
        ret, frame = self.cap.read()

        while(not ret):
            time.sleep(0.01)
            #print(f"[CAMERA - PORT{self.port_num}] Invalid frame, trying again")
            ret, frame = self.cap.read()

        with threading.Lock():
            self.last_frame = frame


    def is_calibrated(self):
        return(self.calibrated)

    def is_recording(self):
        return(self.recording)


    def is_active(self):
        return(self.cap.isOpened())


    def enable_recording(self):
        self.recording = True


    def disable_recording(self):
        with threading.Lock():
            self.recording = False
            self.recording_thread = None


    def __del__(self):
            # Release everything if job is finished
            self.disable_recording()
            self.cap.release()
            self.video_writer.release()
            cv.destroyAllWindows()





if(__name__ == "__main__"):
    cam = Camera(
        camera_name = "test_camera",
        port_num = 0
    )
    cam.calibrate()
    cam.start()

    start_time = time.time()
    while(time.time()-start_time < 10):
        img = cam.read()
        cv.imshow("test", img)
        cv.waitKey(1)
        time.sleep(0.1)
    
    cam.stop()