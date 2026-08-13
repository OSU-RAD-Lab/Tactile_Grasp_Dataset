import pandas as pd
import pathlib
import numpy as np
import scipy.ndimage

class Grasp_Info():
    def __init__(self, data_path):
        # save the data path
        self.data_path = pathlib.Path(data_path)

        self.tactor_labels = [
            "L0", "L1", "L2", "L3", "L4", "L5", "L6",
            "R0", "R1", "R2", "R3", "R4", "R5", "R6",
        ]

        # get the start time from the directory name
        folder_name = str(self.data_path).split('/')[-1]
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




    def transform_tactile_dataframe(self, tactile_df, use_logistic_transform=True):
        readings = dict()
        for tact in self.tactor_labels:
            info = np.array(tactile_df[tact])
            info = scipy.ndimage.median_filter(info, size=20, mode="nearest")

            mean_deviation = info - np.mean(info[0:60])
            mean_deviation[mean_deviation < 0] *= -2.5
            mean_deviation[mean_deviation == 0] = 1

            stdev = np.std(info[0:60])
            if(stdev < 1):
                stdev = 1

            info = mean_deviation / stdev

            if(use_logistic_transform):
                info = 1/(1+np.exp(-1.758*(np.log(info)-3.485))) # based on having logistic fit based on the zero-contact and grasp distributions (mean+2*std for each distribution for the 10% (using zero-contact dist.) and 90% (using grasp dist.) mark)
                #info = 1/(1+np.exp(-1.34*(np.log(info)-2.29))) # based on having logistic fit with 0.1->0.9 cover the tactile reading distribution from the mean to mean+2std
                #info = 1/(1+np.exp(-3.0*np.log(info) + 10)) #based on arbitrary function that looked good with the data
            else:
                info = np.log(info)

            readings[tact] = info
        return(readings)

    def get_transformed_tactile_info(self, use_logistic_transform=True):
        if(not self.is_test):
            tactile_df = self.get_tactile_info()
        else:
            return

        readings = self.transform_tactile_dataframe(tactile_df, use_logistic_transform=use_logistic_transform)
        return(readings)




    def tactile_info_post_transformation(self, transformed_tactile_info):
        tactile_info = []
        for label in self.tactor_labels:
            tactile_info.append(transformed_tactile_info[label])
        tactile_info = np.array(tactile_info)
        tactile_info = tactile_info.transpose()
        return(tactile_info)


    def tactile_to_haptic_info(self, tactile_info):
        dorsal_haptic_info = []
        volar_haptic_info = []
        for row in tactile_info:
            left_data=row[0:7]
            right_data=row[7:14]

            dorsal_row = [
                np.max([left_data[6], 0.5*left_data[5]]), # tip
                np.max([0.5*left_data[5], left_data[4], left_data[3], 0.5*left_data[2]]), # middle
                np.max([0.5*left_data[2], left_data[1], left_data[0]]) # base
            ]
            dorsal_haptic_info.append(dorsal_row)

            volar_row = [
                np.max([right_data[6], 0.5*right_data[5]]), # tip
                np.max([0.5*right_data[5], right_data[4], right_data[3], 0.5*right_data[2]]), # middle
                np.max([0.5*right_data[2], right_data[1], right_data[0]]) # base
            ]
            volar_haptic_info.append(volar_row)

        dorsal_haptic_info = np.array(dorsal_haptic_info)
        volar_haptic_info = np.array(volar_haptic_info)

        def bin_haptic_data(haptic_data, num_bins):
            binned_data = haptic_data*num_bins + 0.5
            binned_data = binned_data.astype(int)
            binned_data = binned_data / num_bins
            return(binned_data)

        dorsal_haptic_info = bin_haptic_data(dorsal_haptic_info, num_bins=5)
        volar_haptic_info = bin_haptic_data(volar_haptic_info, num_bins=5)

        return(dorsal_haptic_info, volar_haptic_info)


    def get_tactile_info_from_grasp(self, start_index=0, end_index=None, use_logistic_transform=True):
        tactile_info = self.get_transformed_tactile_info(use_logistic_transform=use_logistic_transform)
        tactile_info = self.tactile_info_post_transformation(tactile_info)
        return(tactile_info[start_index:end_index])

    def get_haptic_info_from_grasp(self, start_index=0, end_index=None):
        tactile_info = self.get_tactile_info_from_grasp(start_index=start_index, end_index=end_index)
        dorsal_haptic_info, volar_haptic_info = self.tactile_to_haptic_info(tactile_info)
        return(dorsal_haptic_info, volar_haptic_info)


        
