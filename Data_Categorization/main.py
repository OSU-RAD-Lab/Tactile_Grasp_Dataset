import glob
import pathlib
import numpy as np
import pandas as pd
from grasp_info import Grasp_Info
import time
import matplotlib.pyplot as plt
import scipy.ndimage

tactor_labels = [
    "L0", "L1", "L2", "L3", "L4", "L5", "L6",
    "R0", "R1", "R2", "R3", "R4", "R5", "R6",
]

def transform_tactile_dataframe(tactile_df):
    readings = dict()
    for tact in tactor_labels:
        info = np.array(tactile_df[tact])
        info = scipy.ndimage.median_filter(info, size=20, mode="nearest")

        mean_deviation = info - np.mean(info[0:60])
        mean_deviation[mean_deviation < 0] *= -2.5
        mean_deviation[mean_deviation == 0] = 1

        stdev = np.std(info[0:60])
        if(stdev < 1):
            stdev = 1

        info = mean_deviation / stdev
        info = 1/(1+np.exp(-2.8*np.log(info) + 10))

        readings[tact] = info
    return(readings)

def get_transformed_tactile_info(grasp):
    if(not grasp.is_test):
        tactile_df = grasp.get_tactile_info()
    else:
        return

    readings = transform_tactile_dataframe(tactile_df)
    return(readings)
    


def tactile_info_post_transformation(transformed_tactile_info):
    tactile_info = []
    for label in tactor_labels:
        tactile_info.append(transformed_tactile_info[label])
    tactile_info = np.array(tactile_info)
    tactile_info = tactile_info.transpose()
    return(tactile_info)


def tactile_to_haptic_info(tactile_info):
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
    return(dorsal_haptic_info, volar_haptic_info)


def get_activation_values(dorsal_haptic_info, volar_haptic_info):
    concatenated = np.concatenate([dorsal_haptic_info, volar_haptic_info], axis=-1)
    act = np.mean(concatenated, axis=-1)
    return(act)

def get_symmetry_values(dorsal_haptic_info, volar_haptic_info):
    sym = 1 - np.fabs(dorsal_haptic_info - volar_haptic_info)
    sym = np.mean(sym, axis=-1)
    return(sym)

def get_measure_stabilization_value(measure_t):
    measure_std_list = []
    for i in range(0, len(measure_t)-20, 10):
        measure_std_t = np.std(measure_t[i:i+20])
        measure_std_list.append(measure_std_t)
    measure_std = np.mean(measure_std_list)
    return(measure_std)



def get_value_grasp_stability_lists(value_grasp_stability_list):
    value_list = []
    grasp_list = []
    stability_list = []
    for i in range(len(value_grasp_stability_list)):
        value_list.append(value_grasp_stability_list[i][0])
        grasp_list.append(value_grasp_stability_list[i][1])
        stability_list.append(value_grasp_stability_list[i][2])
    return(value_list, grasp_list, stability_list)



def main():
    GRASP_DIR = True

    if(GRASP_DIR):
        path = pathlib.Path(__file__).parents[1] / "Data" / "*" / "*" / "*" / "*" / "*" / "*" / "*"

        save_directory = pathlib.Path(__file__).parents[1] / "Data" / "_grasp_measures"
        save_directory.mkdir(parents=True, exist_ok=True)

        success_dir = save_directory / "SUCCESS"
        success_dir.mkdir(parents=True, exist_ok=True)

        failure_dir = save_directory / "FAILURE"
        failure_dir.mkdir(parents=True, exist_ok=True)
        
        file_names = ["Activation.csv", "Symmetry.csv", "Sym_Act.csv", "Sym_Act_Top.csv", "Sym_Act_Mid.csv", "Sym_Act_Bot.csv"]

        for file_name in file_names:
            with open(str(save_directory / f"{file_name}"), 'w') as csv:
                measure = file_name.split('.')[0]
                csv.write(f"{measure},Outcome,Stability,Object,Size,Material,Interaction,Approach,EEF_Position,Start_Time,\n")

    else:
        path = pathlib.Path(__file__).parents[1] / "dummy_data" / "*.csv"

    activation_list = []
    symmetry_list = []
    symmetry_activation_list = []
    stabilization_list = []
    for x in glob.glob(str(path)):
        print(x)
        if(GRASP_DIR):
            grasp = Grasp_Info(x)
            transformed_tactile_info = get_transformed_tactile_info(grasp)
            if(grasp.is_test):
                continue
        else:
            tactile_df = pd.read_csv(str(x))
            transformed_tactile_info = transform_tactile_dataframe(tactile_df)

        tactile_info = tactile_info_post_transformation(transformed_tactile_info)
        start_index = 160 # 1 second is 20 samples
        dorsal_haptic_info, volar_haptic_info = tactile_to_haptic_info(tactile_info[start_index:])

        act_t = get_activation_values(dorsal_haptic_info, volar_haptic_info)
        sym_t = get_symmetry_values(dorsal_haptic_info, volar_haptic_info)
        sym_act_t = sym_t*act_t

        mean_act = np.mean(act_t)
        act_stability = get_measure_stabilization_value(act_t)

        mean_sym = np.mean(sym_t)
        sym_stability = get_measure_stabilization_value(sym_t)

        mean_sym_act = np.mean(sym_act_t)
        sym_act_stability = get_measure_stabilization_value(sym_act_t)

        if(GRASP_DIR):
            activation_list.append((mean_act, grasp, act_stability))
            symmetry_list.append((mean_sym, grasp, sym_stability))
            symmetry_activation_list.append((mean_sym_act, grasp, sym_act_stability))

        else:
            print(mean_act, mean_sym, mean_sym_act)
            print(act_stability, sym_stability, sym_act_stability)
            plt.plot(dorsal_haptic_info)
            plt.plot(volar_haptic_info)
            plt.show()

    if(GRASP_DIR):
        activation_list = sorted(activation_list, key = lambda x:(-x[0]))
        symmetry_list = sorted(symmetry_list, key = lambda x:(-x[0]))
        symmetry_activation_list = sorted(symmetry_activation_list, key = lambda x:(-x[0]))

        for file_name in file_names:
            measure = file_name.split('.')[0]
            value_list = None
            grasp_list = None
            match(measure):
                case "Activation":
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(activation_list)
                case "Symmetry":
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_list)
                case "Sym_Act":
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list)
                case "Sym_Act_Top":
                    symmetry_activation_list_top = sorted(symmetry_activation_list[0:int(len(symmetry_activation_list)/3)], key = lambda x:(-x[2]))
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_top)
                case "Sym_Act_Mid":
                    symmetry_activation_list_mid = sorted(symmetry_activation_list[int(len(symmetry_activation_list)/3):int(len(symmetry_activation_list)*2/3)], key = lambda x:(-x[2]))
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_mid)
                case "Sym_Act_Bot":
                    symmetry_activation_list_bot = sorted(symmetry_activation_list[int(len(symmetry_activation_list)*2/3):len(symmetry_activation_list)], key = lambda x:(-x[2]))
                    value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_bot)
                case _:
                    raise(Exception(f"Invalid Measure Used: {measure}"))

            for i in range(len(grasp_list)):
                dir_list = str(grasp_list[i].data_path).split('/')
                with open(str(save_directory / f"{grasp_list[i].grasp_outcome}" / f"{file_name}"), 'a') as csv:
                    csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")
                with open(str(save_directory / f"{file_name}"), 'a') as csv:
                    csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")


    #plt.hist(readings, log=True, bins=1000)
    #plt.xscale('log')
    #plt.show()

if(__name__ == "__main__"):
    main()