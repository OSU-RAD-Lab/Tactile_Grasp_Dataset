import time
from sensor_group.tactile import Tactile_Sensor
from sensor_group.camera import Camera

class Sensor_Reader():
    def __init__(self, use_tactile=True, use_wrist_camera=True, use_external_camera=True):
        self.use_tactile = use_tactile
        self.use_wrist_camera = use_wrist_camera
        self.use_external_camera = use_external_camera

        if(self.use_tactile):
            self.tactile = Tactile_Sensor(
                tactile_name = "gripper_tactor",
                port = "/dev/ttyACM0",
                reading_rate_Hz = 20
            )
        else:
            self.tactile = None

        if(self.use_wrist_camera):
            self.wrist_camera = Camera(
                camera_name = "wrist_camera",
                port_num = 8,
                target_fps = 20
            )
        else:
            self.wrist_camera = None

        if(self.use_external_camera):
            self.external_camera = Camera(
                camera_name = "external_camera",
                port_num = 2,
                target_fps = 20
            )
        else:
            self.external_camera = None

        self._initillize_sensors()


    def _initillize_sensors(self):
        if(self.use_tactile):
            # ensure a successful calibration process
            self.tactile.calibrate()

        if(self.use_wrist_camera):
            # ensure the camera is warmed up and a frame can be read from them
            self.wrist_camera.calibrate()

        if(self.use_external_camera):
            # ensure the camera is warmed up and a frame can be read from them
            self.external_camera.calibrate()

    def restart(self):
        self._initillize_sensors()


    def start(self, user_selection):
        # set the path to save the data into
        file_path = user_selection.get_dir_path()
        if(user_selection.test):
            start_time = time.time()
        else:
            start_time = float(str(file_path).split('/')[-1])

        # create the sensor threads
        if(self.use_tactile):
            self.tactile.start(
                concurrency_method = "PROCESS",
                storage_path = file_path,
                start_time = start_time
            )
        else:
            self.tactile_thread = None

        if(self.use_wrist_camera):
            self.wrist_camera.start(
                concurrency_method = "PROCESS",
                storage_path = file_path,
                start_time = start_time
            )
        else:
            self.wrist_camera_thread = None

        if(self.use_external_camera):
            self.external_camera.start(
                concurrency_method = "PROCESS",
                storage_path = file_path,
                start_time = start_time
            )
        else:
            self.external_camera_thread = None

        # give time for processes to begin
        time.sleep(3)


    def stop(self):
        if(self.use_tactile):
            self.tactile.stop()

        if(self.use_wrist_camera):
            self.wrist_camera.stop()

        if(self.external_camera):
            self.external_camera.stop()





if(__name__ == "__main__"):
    from input_handling import User_Selection

    user_selection= User_Selection(test=True)
    user_selection.prompt_all()

    sensor_reader = Sensor_Reader(
        use_tactile = True, 
        use_wrist_camera = True, 
        use_external_camera = True
    )

    sensor_reader.start(user_selection=user_selection)
    time.sleep(10)
    sensor_reader.stop()