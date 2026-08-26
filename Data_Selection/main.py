import glob
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler
import shutil

import sys
sys.path.append(str(pathlib.Path(__file__).parents[1]))
from Data_Categorization.grasp_info import Grasp_Info

def main():
    # Dictionary Ordering: grasp outcome (level 1), sym_act (level 2), instability (level 3)
    selection_dict = {
        "SUCCESS": {
            "TOP": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            },
            "MID": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            },
            "BOT": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            }
        },
        "FAILURE": {
            "TOP": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            },
            "MID": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            },
            "BOT": {
                "TOP": dict(),
                "MID": dict(),
                "BOT": dict()
            }
        }
    }

    data_dir = pathlib.Path(__file__).parents[1] / "Data"

    categorized_data_path = data_dir / "_grasp_measures" / "*" / "*" / "*.csv"
    for path in glob.glob(str(categorized_data_path)):
        labels = path.split('/')
        grasp_outcome_group = labels[-3].upper()
        sym_act_group = labels[-2].split('_')[-1].upper()
        instability_group = labels[-1].split('_')[2].upper()

        head = ["Sym_Act", "Outcome", "Instability", "Object", "Size", "Material", "Interaction", "Approach", "EEF_Position", "Start_Time", "Unnamed: 10"]
        csv_df = pd.read_csv(path, header=0, names=head)
        csv_df = csv_df.drop(columns=["Unnamed: 10"])
        match(instability_group):
            case "TOP":
                grasp_data = csv_df.iloc[0]
            case "MID":
                grasp_data = csv_df.iloc[int((len(csv_df)-0.5)//2)] # if there is no true middle, select the lower index of the 2 middle options
            case "BOT":
                grasp_data = csv_df.iloc[-1]
            case _:
                raise(Exception(f"Error: Invalid instability group: {instability_group}"))

        grasp_measuers = (grasp_data["Sym_Act"], grasp_data["Instability"])
        grasp_path = data_dir / grasp_data["Object"] / grasp_data["Size"] / grasp_data["Material"] / grasp_data["Interaction"] / grasp_data["Approach"] / grasp_data["EEF_Position"] / f"{grasp_data["Start_Time"]:.3f}"

        selection_dict[grasp_outcome_group][sym_act_group][instability_group]["GRASP_DATA"] = Grasp_Info(grasp_path)
        selection_dict[grasp_outcome_group][sym_act_group][instability_group]["GRASP_MEASURES"] = grasp_measuers
        
    for outcome in ["SUCCESS", "FAILURE"]:
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                #selection_dict[outcome][sym_act][instability]["GRASP_DATA"].plot_tactile()
                dorsal_haptic_info, volar_haptic_info = selection_dict[outcome][sym_act][instability]["GRASP_DATA"].get_haptic_info_from_grasp()
                fig, ax = plt.subplots()
                custom_cycler = cycler(linestyle=['-', '--', '-.'])
                ax.set_prop_cycle(custom_cycler)
                ax.plot(dorsal_haptic_info, color="red")
                ax.plot(volar_haptic_info, color="blue")
                ax.set_title(f"{outcome}, {sym_act}, {instability}")
                ax.set_ylim((0,1.1))
                plt.show()

                # Test for the selection code (should match up with manual check)
                print("---")
                print(outcome, sym_act, instability)
                print(str(selection_dict[outcome][sym_act][instability]["GRASP_DATA"].data_path).split('/')[-7:-1])
                print("Sym_Act:", selection_dict[outcome][sym_act][instability]["GRASP_MEASURES"][0])
                print("Instability:", selection_dict[outcome][sym_act][instability]["GRASP_MEASURES"][1])

    print("Copying data to tmp folder...")
    for outcome in ["SUCCESS", "FAILURE"]:
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                # specify the current file
                old_file = selection_dict[outcome][sym_act][instability]["GRASP_DATA"].data_path / "gripper_tactor_tactor_data.csv"
                # specify the new file
                new_filename = f"{outcome}_SymAct_{sym_act}_Instability_{instability}.csv"
                new_dir = pathlib.Path(__file__).parents[1] / "tmp_data"
                new_dir.mkdir(parents=True, exist_ok=True)
                new_file = new_dir / new_filename
                # copy the file over
                shutil.copy(old_file, new_file)
    print("Data copied!")

    # print grasp data
    print("\nGRASP_DATA:")
    for outcome in ["SUCCESS", "FAILURE"]:
        print(f"{outcome}:")
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                print(str(selection_dict[outcome][sym_act][instability]["GRASP_DATA"].data_path).split('/')[-7:-1])

    # print grasp SYM_ACT selection
    print("\nSYM_ACT:")
    for outcome in ["SUCCESS", "FAILURE"]:
        print(f"{outcome}:")
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                print("Sym_Act:", selection_dict[outcome][sym_act][instability]["GRASP_MEASURES"][0])

    # print grasp instability selection
    print("\nINSTABILITY:")
    for outcome in ["SUCCESS", "FAILURE"]:
        print(f"{outcome}:")
        for sym_act in ["TOP", "MID", "BOT"]:
            for instability in ["TOP", "MID", "BOT"]:
                print("Instability:", selection_dict[outcome][sym_act][instability]["GRASP_MEASURES"][1])


# grasp selection list
#GRASP_DATA:
#SUCCESS:
#['CYLINDER', 'LARGE', 'RIGID', 'STRING', 'FRONT', 'CENTER']
#['ASYM_RECT', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CLOSE']
#['CYLINDER', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CLOSE']
#['ASYM_RECT', 'SMALL', 'RIGID', 'STRING', 'FRONT', 'CLOSE']
#['PLANE', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'FAR']
#['CYLINDER', 'SMALL', 'COMPLIANT', 'FREE', 'FRONT', 'CENTER']
#['ASYM_RECT', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CENTER']
#['TRI_PRISM', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CLOSE']
#['TRI_PRISM', 'SMALL', 'COMPLIANT', 'FREE', 'FRONT', 'FAR']
#FAILURE:
#['TRI_PRISM', 'SMALL', 'COMPLIANT', 'STRING', 'FRONT', 'CLOSE']
#['PLANE', 'SMALL', 'COMPLIANT', 'FREE', 'FRONT', 'CENTER']
#['PLANE', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CENTER']
#['TRI_PRISM', 'SMALL', 'COMPLIANT', 'FREE', 'FRONT', 'CLOSE']
#['TRI_PRISM', 'LARGE', 'RIGID', 'FREE', 'FRONT', 'CENTER']
#['ASYM_RECT', 'LARGE', 'RIGID', 'FREE', 'FRONT', 'CLOSE']
#['ASYM_RECT', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'FAR']
#['ASYM_RECT', 'LARGE', 'COMPLIANT', 'STRING', 'FRONT', 'FAR']
#['CYLINDER', 'SMALL', 'RIGID', 'FREE', 'FRONT', 'CLOSE']
#
#SYM_ACT:
#SUCCESS: [0.3492622222222222, 0.2436745406824146, 0.2571475953565506, 0.1870676691729323, 0.1697560975609756, 0.1821516754850088, 0.144306784660767, 0.0902325581395348, 0.0511304347826087]
#FAILURE: [0.1893989071038251, 0.2106386701662292, 0.1884245439469319, 0.0429746281714785, 0.0423728813559322, 0.0331207729468599, 0.0151181102362204, 0.0063541666666666, 0.0]
#
#INSTABILITY:
#SUCCESS: [0.0899955499670544, 0.0513188929951273, 0.0289641077611657, 0.0736374863147658, 0.0277150282536162, 0.0205065711205911, 0.062560858179426, 0.0303262457932384, 0.010783523267423]
#FAILURE: [0.0913983920997523, 0.0505974368175137, 0.0216490210602966, 0.0500050454780254, 0.0400927557973198, 0.0174752138483432, 0.0190910771186585, 0.0134943789610775, 0.0]


if(__name__ == "__main__"):
    main()