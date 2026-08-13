import glob
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler

import sys
sys.path.append(str(pathlib.Path(__file__).parents[1]))
from Data_Categorization.grasp_info import Grasp_Info

def main():
    # Dictionary Ordering: grasp outcome (level 1), sym_act (level 2), instability (level 3)
    selection_dict = {
        "SUCCESS": {
            "TOP": dict(),
            "MID": dict(),
            "BOT": dict()
        },
        "FAILURE": {
            "TOP": dict(),
            "MID": dict(),
            "BOT": dict()
        }
    }

    data_dir = pathlib.Path(__file__).parents[1] / "Data"

    categorized_data_path = data_dir / "_grasp_measures" / "*" / "*" / "*.csv"
    for path in glob.glob(str(categorized_data_path)):
        labels = path.split('/')
        grasp_outcome_group = labels[-3].upper()
        sym_act_group = labels[-2].split('_')[-1].upper()
        instability_group = labels[-1].split('_')[2].upper()

        csv_df = pd.read_csv(path)
        csv_df = csv_df.drop(columns=["Unnamed: 10"])
        match(instability_group):
            case "TOP":
                grasp_data = csv_df.iloc[0]
            case "MID":
                grasp_data = csv_df.iloc[int((len(csv_df)-0.5)//2)] # if there is no middle, select the lower index of the 2 middle options
            case "BOT":
                grasp_data = csv_df.iloc[-1]
            case _:
                raise(Exception(f"Error: Invalid instability group: {instability_group}"))

        # Test for the selection code (should match up with manual check)
        #print("---")
        #print(grasp_outcome_group, sym_act_group, instability_group)
        #print(grasp_data["Object"], grasp_data["Size"], grasp_data["Material"], grasp_data["Interaction"], grasp_data["Approach"], grasp_data["EEF_Position"], grasp_data["Start_Time"])

        grasp_path = data_dir / grasp_data["Object"] / grasp_data["Size"] / grasp_data["Material"] / grasp_data["Interaction"] / grasp_data["Approach"] / grasp_data["EEF_Position"] / f"{grasp_data["Start_Time"]:.3f}"

        selection_dict[grasp_outcome_group][sym_act_group][instability_group] = Grasp_Info(grasp_path)
        
    for outcome in ["SUCCESS", "FAILURE"]:
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                dorsal_haptic_info, volar_haptic_info = selection_dict[outcome][sym_act][instability].get_haptic_info_from_grasp()
                fig, ax = plt.subplots()
                custom_cycler = cycler(linestyle=['-', '--', '-.'])
                ax.set_prop_cycle(custom_cycler)
                ax.plot(dorsal_haptic_info, color="red")
                ax.plot(volar_haptic_info, color="blue")
                ax.set_title(f"{outcome}, {sym_act}, {instability}")
                plt.show()





if(__name__ == "__main__"):
    main()