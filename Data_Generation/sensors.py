import threading
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
                port = "/dev/ttyACM0"
            )
        else:
            self.tactile = None

        if(self.use_wrist_camera):
            self.wrist_camera = Camera(
                camera_name = "wrist_camera",
                port_num = 6
            )
        else:
            self.wrist_camera = None

        if(self.use_external_camera):
            self.external_camera = Camera(
                camera_name = "external_camera",
                port_num = 2
            )
        else:
            self.external_camera = None

        self.initillize_sensors()


    def initillize_sensors(self):
        if(self.use_tactile):
            # ensure a successful calibration process
            self.tactile.calibrate()
            self.tactile.start()

        if(self.use_wrist_camera):
            # ensure the camera is warmed up and a frame can be read from them
            self.wrist_camera.calibrate()
            self.wrist_camera.start()

        if(self.use_external_camera):
            # ensure the camera is warmed up and a frame can be read from them
            self.external_camera.calibrate()
            self.external_camera.start()


    def start(self, user_selection):
        # set the path to save the data into
        file_path = user_selection.get_dir_path()
        if(user_selection.test):
            start_time = time.perf_counter()
        else:
            start_time = float(str(file_path).split('/')[-1])

        # create the sensor threads
        if(self.use_tactile):
            self.tactile_thread = self.create_tactile_thread(self.tactile, file_path, start_time)
            self.tactile.enable_recording()
            self.tactile_thread.start()
        else:
            self.tactile_thread = None

        if(self.use_wrist_camera):
            self.wrist_camera_thread = self.create_camera_thread(self.wrist_camera, file_path, start_time)
            self.wrist_camera.enable_recording()
            self.wrist_camera_thread.start()
        else:
            self.wrist_camera_thread = None

        if(self.use_external_camera):
            self.external_camera_thread = self.create_camera_thread(self.external_camera, file_path, start_time)
            self.external_camera.enable_recording()
            self.external_camera_thread.start()
        else:
            self.external_camera_thread = None


    def stop(self):
        if(self.use_tactile):
            self.tactile.disable_recording()

        if(self.use_wrist_camera):
            self.wrist_camera.disable_recording()

        if(self.external_camera):
            self.external_camera.disable_recording()


    def create_tactile_thread(self, tactile_obj, path, start_time):
        tactor_data_file_path = path / f"{tactile_obj.tactile_name}_tactor_data.csv"
        tactile_thread = threading.Thread(target=self.tactile_read, args=(tactile_obj, tactor_data_file_path, start_time))
        return(tactile_thread)


    def tactile_read(self, tactile_obj, tactile_record_path, start_time):
        try:
            with threading.Lock():
                csv_data_saver = open(str(tactile_record_path), "w")
                csv_data_saver.write("time_s,L6,L5,L4,L3,L2,L1,L0,R6,R5,R4,R3,R2,R1,R0,\n")

            while(tactile_obj.is_recording()):
                process_start_time = time.perf_counter()

                # write the frame and frame data
                with threading.Lock():
                    tactor_data = tactile_obj.read(output_raw_data=True)

                tactor_data_string = ""
                for d in tactor_data:
                    tactor_data_string += f"{d},"
                csv_data_saver.write(f"{process_start_time-start_time:.3f},{tactor_data_string}\n")

                # compute time until next frame
                process_end_time = time.perf_counter()
                process_time = process_end_time - process_start_time
                remaining_time = tactile_obj.read_period - process_time
                if(remaining_time >= 0):
                    time.sleep(remaining_time)
                else:
                    print(f"WARNING: {tactile_obj.tactile_name} has a negative wait time until next read (skipping wait)")

        except Exception as e:
            print("-------------------------")
            print(e)
            print("-------------------------")
            with threading.Lock():
                tactile_obj.disable_recording()
        finally:
            csv_data_saver.close()


    def create_camera_thread(self, camera_obj, path, start_time):
        camera_obj.create_video_writer(path)
        frame_data_file_path = path / f"{camera_obj.camera_name}_frame_data.csv"
        camera_thread = threading.Thread(target=self.camera_read, args=(camera_obj, frame_data_file_path, start_time))
        return(camera_thread)


    def camera_read(self, camera_obj, frame_data_record_path, start_time):
        try:
            with threading.Lock():
                frame_number = 0
                csv_frametracker = open(str(frame_data_record_path), "w")
                csv_frametracker.write("frame_num,time_s,\n")

            while(camera_obj.is_active() and camera_obj.is_recording()):
                process_start_time = time.perf_counter()

                # write the frame and frame data
                with threading.Lock():
                    frame = camera_obj.read()
                    camera_obj.video_writer.write(frame)

                csv_frametracker.write(f"{frame_number},{process_start_time-start_time:.3f},\n")
                frame_number += 1

                # compute time until next frame
                process_end_time = time.perf_counter()
                process_time = process_end_time - process_start_time
                remaining_time = camera_obj.inter_frame_period - process_time
                #print(camera_obj.inter_frame_period, remaining_time)
                if(remaining_time >= 0):
                    time.sleep(remaining_time)
                else:
                    print(f"WARNING: {camera_obj.camera_name} has a negative wait time until next read (skipping wait)")

        except Exception as e:
            print("-------------------------")
            print(e)
            print("-------------------------")
            with threading.Lock():
                camera_obj.disable_recording()
        finally:
            csv_frametracker.close()

            



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