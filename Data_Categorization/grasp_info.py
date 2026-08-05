import pandas as pd
import pathlib

class Grasp_Info():
    def __init__(self, data_path):
        # save the data path
        self.data_path = pathlib.Path(data_path)

        # get the start time from the directory name
        folder_name = data_path.split('/')[-1]
        if(folder_name == "test"):
            self.start_time = 0
            self.is_test = True
        else:
            self.start_time = float(folder_name)
            self.is_test = False


        # specify the external camera files
        self.external_camera_frames_csv = self.data_path / "external_camera_frame_data.csv"
        self.external_camera_video_mp4 = self.data_path / "external_camera_frame_video.mp4"
        # specify the wrist camera files
        self.wrist_camera_frames_csv = self.data_path / "wrist_camera_frame_data.csv"
        self.wrist_camera_video_mp4 = self.data_path / "wrist_camera_video.mp4"
        # specify the tactile data file
        self.tactile_data_csv = self.data_path / "gripper_tactor_tactor_data.csv"

        # get the outcome of the grasp
        with open(str(self.data_path / "grasp_outcome.txt"), 'r') as outcome_txt:
            self.grasp_outcome = outcome_txt.readline()
        match(self.grasp_outcome):
            case "SUCCESS":
                self.grasp_succeeded = True
            case "FAILURE":
                self.grasp_succeeded = False
            case _:
                raise(Exception("ERROR: Grasp outcome was not properly defined!"))

    def _get_tactile_path(self):
        return(str(self.tactile_data_csv))

    def get_tactile_info(self):
        tactile_dataframe = pd.read_csv(self._get_tactile_path())
        tactile_dataframe = tactile_dataframe.drop(columns=["Unnamed: 15"])
        return(tactile_dataframe)

    def get_grasp_outcome(self):
        return(self.grasp_outcome)



        
