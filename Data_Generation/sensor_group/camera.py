# code modified from OpenCv's Documentation: https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
import cv2 as cv
import threading
import multiprocessing
import time
import pathlib
import matplotlib.pyplot as plt
import signal

class Camera():
    def __init__(self, camera_name, port_num, target_fps):
        self.camera_name = camera_name.replace(" ", "_")

        self.port_num = port_num
        self.cap = cv.VideoCapture(self.port_num)

        target_fps = target_fps
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
        self.destroy_video_writer() # destroy previous video writer if it exists
        self.video_writer = cv.VideoWriter(str(video_file_path), self.fourcc, self.cap_fps, self.cap_dim)
        return(self.video_writer)

    def destroy_video_writer(self):
        if(self.video_writer is not None):
            self.video_writer.release()
            self.video_writer = None



    def calibrate(self):
        print(f"[{self.camera_name}] Calibrating camera...")
        # give some time to boot up
        time.sleep(3)
        # ensure there is a starting frame before recording
        self.get_next_frame()
        self.calibrated = True
        print(f"[{self.camera_name}] Camera calibrated")


    def start(self, concurrency_method, storage_path=None, start_time=None):
        print(f"[{self.camera_name}] Starting camera...")
        if(self.is_recording()):
            print(f"[{self.camera_name}] Camera already started")
            return
        
        if(not self.is_calibrated()):
            print(f"[{self.camera_name}] Camera not calibrated...")
            self.calibrate()

        self.enable_recording(concurrency_method)

        match(concurrency_method.upper()):
            case "THREAD":
                print(f"[{self.camera_name}] Starting camera thread")
                self.start_data_thread()
            case "PROCESS":
                print(f"[{self.camera_name}] Starting camera process")
                self.start_recording_process(storage_path, start_time)
            case _:
                raise(Exception(f"Invalid Concurrency Method: {concurrency_method}"))



    def start_data_thread(self):
        self.recording_thread = threading.Thread(target=self.gather_readings, args=())
        self.recording_thread.start()

    def gather_readings(self):
        print(f"[{self.camera_name}] Recording started @ {self.cap_fps} FPS")
        while(self.is_recording() and self.is_active()):
            self.get_next_frame()



    def start_recording_process(self, storage_path, start_time):
        if(storage_path == None):
            print("WARNING: Using default path to save camera recording")
            storage_path = pathlib.Path(__file__).parent / "data" / "camera"
            storage_path.mkdir(exist_ok=True, parents=True)
        if(start_time == None):
            start_time = 0

        self.camera_recording_process = multiprocessing.Process(target=self.record_readings, args=(storage_path, start_time))
        self.camera_recording_process.start()

    def record_readings(self, storage_path, start_time):
        try:
            signal.signal(signal.SIGTERM, self.exit_exception)
            self.create_video_writer(storage_path)
            frame_data_path = storage_path / f"{self.camera_name}_frame_data.csv"
            frame_number = 0
            with open(str(frame_data_path), "w") as csv_frametracker:
                csv_frametracker.write("frame_num,time_s,\n")

            while(self.is_active() and self.is_recording()):
                process_start_time = time.time()

                # get the frame data
                ret, frame = self.cap.read()
                while(not ret):
                    print(f"[{self.camera_name}] Invalid frame, trying again")
                    ret, frame = self.cap.read()
                # write the frame data
                self.video_writer.write(frame)

                with open(str(frame_data_path), "a") as csv_frametracker:
                    csv_frametracker.write(f"{frame_number},{process_start_time-start_time:.3f},\n")
                frame_number += 1

                # compute time until next frame
                process_end_time = time.time()
                process_time = process_end_time - process_start_time
                remaining_time = self.inter_frame_period - process_time
                if(remaining_time >= 0):
                    time.sleep(remaining_time)
                else:
                    print(f"WARNING: {self.camera_name} has a negative wait time until next read (skipping wait)")

        except Exception as e:
            print("-------------------------")
            print("EXCEPTION:", e)
            print("-------------------------")
        finally:
            print(f"[{self.camera_name}] STOPPING PROCESS")
            self.destroy_video_writer()

    # code modified from https://stackoverflow.com/questions/42560706/how-to-execute-code-just-before-terminating-the-process-in-python
    def exit_exception(self, *args):
        print(f"[{self.camera_name}] TERMINATING PROCESS")
        raise(Exception("Termination Exception: needed to exit process"))



    def get_next_frame(self):
        ret, frame = self.cap.read()
        while(not ret):
            print(f"[{self.camera_name}] Invalid frame, trying again")
            ret, frame = self.cap.read()

        self.last_frame = frame


    def stop(self):
        if(not self.is_recording()):
            print(f"[{self.camera_name}] trying to stop camera when it is not started (skipping command)")
            return

        self.disable_recording()
    
        match(self.concurrency_method):
            case "THREAD":
                print(f"[{self.camera_name}] Stoping camera thread")

            case "PROCESS":
                print(f"[{self.camera_name}] stopping camera process")
                self.camera_recording_process.terminate()

            case _:
                raise(Exception(f"Invalid Concurrency Method: {self.concurrency_method}"))


    def read(self):
        return(self.last_frame)



    def is_calibrated(self):
        return(self.calibrated)

    def is_recording(self):
        return(self.recording)


    def is_active(self):
        return(self.cap.isOpened())


    def enable_recording(self, concurrency_method):
        self.recording = True
        self.concurrency_method = concurrency_method.upper()


    def disable_recording(self):
        with threading.Lock():
            self.recording = False
            self.recording_thread = None


    def __del__(self):
            # Release everything if job is finished
            self.disable_recording()
            self.destroy_video_writer()
            self.cap.release()
            cv.destroyAllWindows()





if(__name__ == "__main__"):
    cam = Camera(
        camera_name = "test_camera",
        port_num = 0,
        target_fps = 24
    )

    cam.calibrate()

    test = "PROCESS"
    if(test.upper() == "THREAD"):
        cam.start(concurrency_method = "THREAD")
        start_time = time.time()
        while(time.time()-start_time < 10):
            img = cam.read()
            cv.imshow("test", img)
            cv.waitKey(1)
            time.sleep(1/cam.cap_fps)
        cam.stop()

    elif(test.upper() == "PROCESS"):
        cam.start(concurrency_method = "PROCESS")
        time.sleep(10)
        cam.stop()