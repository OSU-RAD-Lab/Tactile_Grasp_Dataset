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
    



def main():
    GRASP_DIR = False

    if(GRASP_DIR):
        path = pathlib.Path(__file__).parents[1] / "Data" / "*" / "*" / "*" / "*" / "*" / "*" / "*"
    else:
        path = pathlib.Path(__file__).parents[1] / "dummy_data" / "*.csv"

    for x in glob.glob(str(path)):
        print(x)
        if(GRASP_DIR):
            grasp = Grasp_Info(x)
            transformed_tactile_info = get_transformed_tactile_info(grasp)
        else:
            tactile_df = pd.read_csv(str(x))
            transformed_tactile_info = transform_tactile_dataframe(tactile_df)


        tatile_info = []
        for label in tactor_labels:
            tatile_info.append(transformed_tactile_info[label])
        tatile_info = np.array(tatile_info)
        tatile_info = tatile_info.transpose()

        dorsal_haptic_info = []
        volar_haptic_info = []
        for row in tatile_info:
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

        plt.plot(dorsal_haptic_info)
        plt.plot(volar_haptic_info)
        plt.show()
                
        #plt.plot(info)
        #plt.title(f"{grasp.grasp_outcome}: {x.split('/', 7)[-1]}")
        #plt.show()


    plt.hist(readings, log=True, bins=1000)
    #plt.xscale('log')
    plt.show()

if(__name__ == "__main__"):
    main()