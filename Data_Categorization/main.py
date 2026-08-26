import glob
import pathlib
import numpy as np
import pandas as pd
from grasp_info import Grasp_Info
import matplotlib.pyplot as plt
import scipy.ndimage
import scipy.stats

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

def get_measure_stabilization_value(measure_t, one_second_sample_size=5, jump_distance=3):
    measure_std_list = []
    for i in range(0, len(measure_t)-one_second_sample_size, jump_distance):
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



def separate_success_and_failure(value_grasp_stability_list):
    success_list = []
    failure_list = []
    for item in value_grasp_stability_list:
        if(item[1].grasp_outcome == "SUCCESS"):
            success_list.append(item)
        elif(item[1].grasp_outcome == "FAILURE"):
            failure_list.append(item)
        else:
            raise(Exception(f"Invalid grasp outcome detected: {item[1].grasp_outcome}"))

    return(success_list, failure_list)


def get_boundary_indecies(measure_list, val_grasp_stability_selection=0):
    measure_list = sorted(measure_list, key = lambda x:(-x[val_grasp_stability_selection]))
    val_grasp_stability_lists = get_value_grasp_stability_lists(measure_list)
    median = np.median(val_grasp_stability_lists[val_grasp_stability_selection]) # already sorted (greatest to least)
    mad = scipy.stats.median_abs_deviation(val_grasp_stability_lists[val_grasp_stability_selection])
    boundaries = [median+mad,  median+0.5*mad, median-0.5*mad, median-mad]

    indecies = []
    for i in range(len(val_grasp_stability_lists[val_grasp_stability_selection])):
        # wait until the value is less than the boundary
        if(val_grasp_stability_lists[val_grasp_stability_selection][i] < boundaries[len(indecies)]):
            indecies.append(i)
            if(len(indecies) == len(boundaries)):
                return(indecies)
    
    while(len(indecies) != len(boundaries)):
        indecies.append(-1)

    return(indecies)



def plot_median_with_deviations(measure_list, name, plt_show=True, show_median_lines=True):
    plt.hist(measure_list, bins=50)
    median = np.median(measure_list)
    mad = scipy.stats.median_abs_deviation(measure_list)
    if(show_median_lines):
        plt.vlines([median+mad, median+0.5*mad, median-0.5*mad, median-mad], colors="red", ymin=0, ymax=10)
    plt.xlabel("grasp measure")
    plt.ylabel("count")
    plt.title(name)
    if(plt_show):
        plt.show()


def main():
    path = pathlib.Path(__file__).parents[1] / "Data" / "*" / "*" / "*" / "*" / "*" / "*" / "*"

    save_directory = pathlib.Path(__file__).parents[1] / "Data" / "_grasp_measures"
    save_directory.mkdir(parents=True, exist_ok=True)

    success_dir = save_directory / "SUCCESS"
    success_dir.mkdir(parents=True, exist_ok=True)
    success_sym_act_top_dir = success_dir / "SYM_ACT_TOP"
    success_sym_act_top_dir.mkdir(parents=True, exist_ok=True)
    success_sym_act_mid_dir = success_dir / "SYM_ACT_MID"
    success_sym_act_mid_dir.mkdir(parents=True, exist_ok=True)
    success_sym_act_bot_dir = success_dir / "SYM_ACT_BOT"
    success_sym_act_bot_dir.mkdir(parents=True, exist_ok=True)

    failure_dir = save_directory / "FAILURE"
    failure_dir.mkdir(parents=True, exist_ok=True)
    failure_sym_act_top_dir = failure_dir / "SYM_ACT_TOP"
    failure_sym_act_top_dir.mkdir(parents=True, exist_ok=True)
    failure_sym_act_mid_dir = failure_dir / "SYM_ACT_MID"
    failure_sym_act_mid_dir.mkdir(parents=True, exist_ok=True)
    failure_sym_act_bot_dir = failure_dir / "SYM_ACT_BOT"
    failure_sym_act_bot_dir.mkdir(parents=True, exist_ok=True)
    
    file_names = ["Activation.csv", "Symmetry.csv", "Sym_Act.csv", "Sym_Act_Top.csv", "Sym_Act_Mid.csv", "Sym_Act_Bot.csv"]

    for file_name in file_names:
        measure = file_name.split('.')[0]
        with open(str(save_directory / f"{file_name}"), 'w') as csv:
            csv.write(f"{measure},Outcome,Instability,Object,Size,Material,Interaction,Approach,EEF_Position,Start_Time,\n")
        if(measure.startswith("Sym_Act_")):
            # SUCCESS/FAILURE grouping
            outcome_naming = ["Success", "Failure"]
            for outcome_name in outcome_naming:
                with open(str(save_directory / f"{outcome_name.upper()}" / f"{outcome_name}_{file_name}"), 'w') as csv:
                    csv.write(f"{measure},Outcome,Instability,Object,Size,Material,Interaction,Approach,EEF_Position,Start_Time,\n")

                # SYM_ACT (TOP/MID/BOT) grouping
                instability_naming = ["Top", "Mid", "Bot"]
                for instability_name in instability_naming:
                    with open(str(save_directory / f"{outcome_name.upper()}" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"{outcome_name}_Instable_{instability_name}_{file_name}"), 'w') as csv:
                        csv.write(f"{measure},Outcome,Instability_{instability_name},Object,Size,Material,Interaction,Approach,EEF_Position,Start_Time,\n")

    activation_list = []
    symmetry_list = []
    symmetry_activation_list = []
    haptic_signals = None
    tactile_signal = []
    tactile_signals1 = []
    tactile_signals2 = []
    use_logistic_transform = True
    show_haptic_plots = False
    for x in glob.glob(str(path)):
        print(x)
        grasp = Grasp_Info(x)

        if(grasp.is_test):
            continue

        # 1 second is 20 samples
        # No-Grasp Distribution: 0->100 (mean: -0.122, std: 1.176) -> make mean+2*std = 2.23 the 10% point in logistic function
        # Grasp Distribution: 300->500 (mean: 1.230, std: 1.755) -> make mean+2*std = 4.74 the 90% point
        start_index = 0
        end_index = None
        tactile_info = grasp.get_tactile_info_from_grasp(start_index=start_index, end_index=end_index, use_logistic_transform=use_logistic_transform)
        
        #plt.plot(tactile_info)
        #plt.show()
        
        tmp = tactile_info.flatten()
        tmp1 = tactile_info[0:150].flatten()
        tmp2 = tactile_info[350:500].flatten()

        tactile_signal = np.append(tactile_signal, tmp)
        tactile_signals1 = np.append(tactile_signals1, tmp1)
        tactile_signals2 = np.append(tactile_signals2, tmp2)

        dorsal_haptic_info, volar_haptic_info = grasp.get_haptic_info_from_grasp(start_index=start_index)
        if(haptic_signals is None):
            haptic_signals = np.append(volar_haptic_info.flatten(), dorsal_haptic_info.flatten())
        else:
            tmp = np.append(volar_haptic_info.flatten(), dorsal_haptic_info.flatten())
            haptic_signals = np.append(haptic_signals, tmp)

        act_t = get_activation_values(dorsal_haptic_info, volar_haptic_info)
        sym_t = get_symmetry_values(dorsal_haptic_info, volar_haptic_info)
        sym_act_t = sym_t*act_t

        if(show_haptic_plots):
            plt.plot(dorsal_haptic_info)
            plt.plot(volar_haptic_info)
            plt.title(f"{grasp.grasp_outcome}")
            plt.show()

        #plt.plot(sym_act_t)
        #plt.title(f"{grasp.grasp_outcome}")
        #plt.show()

        mean_act = np.mean(act_t)
        act_stability = get_measure_stabilization_value(act_t, one_second_sample_size=5, jump_distance=3)

        mean_sym = np.mean(sym_t)
        sym_stability = get_measure_stabilization_value(sym_t, one_second_sample_size=5, jump_distance=3)

        mean_sym_act = np.mean(sym_act_t)
        sym_act_stability = get_measure_stabilization_value(sym_act_t, one_second_sample_size=5, jump_distance=3)

        activation_list.append((mean_act, grasp, act_stability))
        symmetry_list.append((mean_sym, grasp, sym_stability))
        symmetry_activation_list.append((mean_sym_act, grasp, sym_act_stability))

    #plt.hist(tactile_signal, bins=20)
    #plt.title("Tactile Info")
    #plt.show()

    if(not use_logistic_transform):
        #stat, p = scipy.stats.normaltest(tactile_signals1)
        #print(f"NORM RESULTS: {stat}, p={p}")
        #print("pos")
        #pos_tmp = np.log(tactile_signals1[tactile_signals1>0])
        #print(f"MEAN: {np.mean(pos_tmp)} +/- {np.std(pos_tmp)}")
        #print(f"MEDIAN: {np.median(pos_tmp)} +/- {scipy.stats.median_abs_deviation(pos_tmp)}")
        #p99_99_pos = np.percentile(pos_tmp, 99.99)
        #print(f"99.99th-PERCENTILE: {p99_99_pos} (below {(1-0.9999)*len(pos_tmp)} values)")
        #print("neg")
        #neg_tmp = np.log(-tactile_signals1[tactile_signals1<0])
        #print(f"MEAN: {np.mean(neg_tmp)} +/- {np.std(neg_tmp)}")
        #print(f"MEDIAN: {np.median(neg_tmp)} +/- {scipy.stats.median_abs_deviation(neg_tmp)}")
        #p99_99_neg = np.percentile(neg_tmp, 99.99)
        #print(f"99.99th-PERCENTILE: {p99_99_neg} (below {(1-0.9999)*len(neg_tmp)} values)")
        #plt.hist(pos_tmp, bins=500)
        #plt.show()
        #plt.hist(neg_tmp, bins=500)
        #plt.show()

        plt.hist(np.log(tactile_signal), bins=500)
        plt.title("Tactile Info")
        plt.show()

        tactile_signals1[tactile_signals1<0] *= -1

        # 99 PERCENTILE FOR zero-contact 
        p99 = np.percentile(tactile_signals1, 99)
        print(f"99th-PERCENTILE (noise): {p99} (below {(1-0.99)*len(tactile_signals1)} values)")
        plotting_data = tactile_signals1[tactile_signals1 < 2*p99]
        plt.hist(plotting_data, bins=500)
        plt.xlim((0, 2*p99 + 0.5))
        plt.show()
        
        
        # 99.9 PERCENTILE FOR zero-contact 
        p99_9 = np.percentile(tactile_signals1, 99.9)
        print(f"99.9th-PERCENTILE (noise): {p99_9} (below {(1-0.999)*len(tactile_signals1)} values)")
        plotting_data = tactile_signals1[tactile_signals1 < 2*p99_9]
        plt.hist(plotting_data, bins=500)
        plt.xlim((0, 2*p99_9 + 0.5))
        plt.show()

        # 99.95 PERCENTILE FOR zero-contact 
        p99_95 = np.percentile(tactile_signals1, 99.95)
        print(f"99.95th-PERCENTILE (noise): {p99_95} (below {(1-0.9995)*len(tactile_signals1)} values)")
        plotting_data = tactile_signals1[tactile_signals1 < 2*p99_95]
        plt.hist(plotting_data, bins=500)
        plt.xlim((0, 2*p99_95 + 0.5))
        plt.show()

        # 99.999 PERCENTILE FOR zero-contact 
        p99_99 = np.percentile(tactile_signals1, 99.99)
        print(f"99.99th-PERCENTILE (noise): {p99_99} (below {(1-0.9999)*len(tactile_signals1)} values)")
        plotting_data = tactile_signals1[tactile_signals1 < 2*p99_99]
        plt.hist(plotting_data, bins=500)
        plt.xlim((0, 2*p99_99 + 0.5))
        plt.show()

        print("---")
        print("---")
        print("---")

        #stat, p = scipy.stats.normaltest(tactile_signals2)
        #print(f"NORM RESULTS: {stat}, p={p}")
        #print("pos")
        #pos_tmp = np.log(tactile_signals2[tactile_signals2>5])
        #print(f"MEAN: {np.mean(pos_tmp)} +/- {np.std(pos_tmp)}")
        #print(f"MEDIAN: {np.median(pos_tmp)} +/- {scipy.stats.median_abs_deviation(pos_tmp)}")
        #print(f"90th-PERCENTILE: {np.percentile(pos_tmp, 90)}")
        #print("neg")
        #neg_tmp = np.log(-tactile_signals2[tactile_signals2<-5])
        #print(f"MEAN: {np.mean(neg_tmp)} +/- {np.std(neg_tmp)}")
        #print(f"MEDIAN: {np.median(neg_tmp)} +/- {scipy.stats.median_abs_deviation(neg_tmp)}")
        #print(f"90th-PERCENTILE: {np.percentile(neg_tmp, 90)}")
        #plt.hist(pos_tmp, bins=500)
        #plt.show()
        #plt.hist(neg_tmp, bins=500)
        #plt.show()


        noise_value = p99_9
        def get_and_plot_percentile(data, p, name):
            # 10th percentile for contact
            p_contact = np.percentile(data, p)
            print(f"{p}th-PERCENTILE ({name}): {p_contact} (above {(p/100)*len(data)} values)")

        # positive percentiles for contact
        combo_signal = np.fabs(tactile_signals2[np.fabs(tactile_signals2) > noise_value])
        for p in range(0, 99, 5):
            get_and_plot_percentile(combo_signal, p, name="contact")

        pos_signal = tactile_signals2[tactile_signals2 > noise_value]
        for p in range(0, 55, 10):
            get_and_plot_percentile(pos_signal, p, name="pos_contact")

        neg_signal = -(tactile_signals2[tactile_signals2 < -noise_value])
        for p in range(0, 55, 10):
            get_and_plot_percentile(neg_signal, p, name="neg_contact")
        

        # plotting percentile differences between positive and negative activation
        plotting_data = []
        diff_plot = []
        for i in range(1,99):
            pos_p = np.percentile(pos_signal, i)
            neg_p = np.percentile(neg_signal, i)
            plotting_data.append((pos_p, neg_p))
            diff_plot.append(pos_p-neg_p)
        plt.plot(plotting_data)
        plt.show()
        plt.plot(diff_plot)
        plt.show()




        #tmp = [tactile_signals1[tactile_signals1>0], tactile_signals2[tactile_signals2>5]]
        #counts, bins, patches = plt.hist(tmp, bins=500, stacked=True)
        #plt.title("tactile_readings (positive)")
        #plt.show()
        #p = counts[1]/(counts[1]+counts[0])
        #bins = bins[0:len(bins)-1]
        #plt.plot(bins, p)
        #plt.show()

        #tmp = [tactile_signals1[tactile_signals1<0], tactile_signals2[tactile_signals2<-5]]
        #counts, bins, patches = plt.hist(tmp, bins=500, stacked=True)
        #plt.title("tactile_readings negative")
        #plt.show()
        #p = counts[1]/(counts[1]+counts[0])
        #bins = bins[0:len(bins)-1]
        #plt.plot(bins, p)
        #plt.show()


    activation_list = sorted(activation_list, key = lambda x:(-x[0]))
    symmetry_list = sorted(symmetry_list, key = lambda x:(-x[0]))
    symmetry_activation_list = sorted(symmetry_activation_list, key = lambda x:(-x[0]))
    # ALL Grasp indicies
    bound_indecies = get_boundary_indecies(symmetry_activation_list)

    success_selected_sym_act_list = [0.2054273504273504, 0.1889988998899889, 0.1858823529411764, 0.1511957671957671, 0.1321703011422637, 0.1397979797979798, 0.1043757159221076, 0.097679012345679, 0.0196679438058748]
    failure_selected_sym_act_list = [0.1039243498817966, 0.0931481481481481, 0.1286222222222222, 0.0571941638608305, 0.0537915234822451, 0.0363201911589008, 0.0153703703703703, 0.0058810325476992, 0.0]

    success_selected_instability_list = [0.0476363849388943, 0.0249372779971495, 0.0189279464334645, 0.0498170190826048, 0.0287769806635314, 0.0154176300811168, 0.0458752468147867, 0.0192980348524485, 0.0028174815110276]
    failure_selected_instability_list = [0.0549709794478634, 0.0409702125429735, 0.0191070391259324, 0.0513309806000732, 0.0374712153500157, 0.0172237624378151, 0.0183380941395327, 0.010236383297605, 0.0]

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

                plot_median_with_deviations(value_list, name="Sym_Act all", plt_show=False)
                plt.vlines(success_selected_sym_act_list, ymin=0, ymax=8, colors="Green", linewidth=3, linestyles="--")
                plt.vlines(failure_selected_sym_act_list, ymin=0, ymax=8, colors="Red", linewidth=3, linestyles="--")
                plt.show()

                plot_median_with_deviations(stability_list, name="stable all", plt_show=False)
                plt.vlines(success_selected_instability_list, ymin=0, ymax=8, colors="Green", linewidth=3, linestyles="--")
                plt.vlines(failure_selected_instability_list, ymin=0, ymax=8, colors="Red", linewidth=3, linestyles="--")
                plt.show()
            case "Sym_Act_Top":
                symmetry_activation_list_top = sorted(symmetry_activation_list[0:bound_indecies[0]], key = lambda x:(-x[2]))
                value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_top)
                #plot_median_with_deviations(value_list, name="sym_act sym_act_top all")
                #plot_median_with_deviations(stability_list, name="stable sym_act_top all")
            case "Sym_Act_Mid":
                symmetry_activation_list_mid = sorted(symmetry_activation_list[bound_indecies[1]:bound_indecies[2]], key = lambda x:(-x[2]))
                value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_mid)
                #plot_median_with_deviations(value_list, name="sym_act sym_act_mid all")
                #plot_median_with_deviations(stability_list, name="stable sym_act_mid all")
            case "Sym_Act_Bot":
                symmetry_activation_list_bot = sorted(symmetry_activation_list[bound_indecies[3]:len(symmetry_activation_list)], key = lambda x:(-x[2]))
                value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list_bot)
                #plot_median_with_deviations(value_list, name="sym_act sym_act_bot all")
                #plot_median_with_deviations(stability_list, name="stable sym_act_bot all")
            case _:
                raise(Exception(f"Invalid Measure Used: {measure}"))

        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to general directory
            with open(str(save_directory / f"{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")


    # Separate successful and failed grasps
    sym_act_success_list, sym_act_failure_list = separate_success_and_failure(symmetry_activation_list)
    # SUCCESS Grasps
    success_bound_indecies = get_boundary_indecies(sym_act_success_list)
    # FAILURE Grasps
    failure_bound_indecies = get_boundary_indecies(sym_act_failure_list)

    for file_name in file_names:
        measure = file_name.split('.')[0]
        value_list = None
        grasp_list = None
        match(measure):
            case "Activation":
                continue #value_list, grasp_list, stability_list = get_value_grasp_stability_lists(activation_list)
            case "Symmetry":
                continue #value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_list)
            case "Sym_Act":
                # SUCCESS Plots
                success_value_list, success_grasp_list, success_stability_list = get_value_grasp_stability_lists(sym_act_success_list)
                plot_median_with_deviations(success_value_list, name="sym_act success", plt_show=False)
                plt.vlines(success_selected_sym_act_list, ymin=0, ymax=8, colors="Green", linewidth=3, linestyles="--")
                plt.show()

                plot_median_with_deviations(success_stability_list, name="instable success", plt_show=False, show_median_lines=False)
                plt.vlines(success_selected_instability_list, ymin=0, ymax=8, colors="Green", linewidth=3, linestyles="--")
                plt.show()

                # FAILURE Plots
                failure_value_list, failure_grasp_list, failure_stability_list = get_value_grasp_stability_lists(sym_act_failure_list)
                plot_median_with_deviations(failure_value_list, name="sym_act failure", plt_show=False)
                plt.vlines(failure_selected_sym_act_list, ymin=0, ymax=8, colors="Red", linewidth=3, linestyles="--")
                plt.show()

                plot_median_with_deviations(failure_stability_list, name="instable failure", plt_show=False, show_median_lines=False)
                plt.vlines(failure_selected_instability_list, ymin=0, ymax=8, colors="Red", linewidth=3, linestyles="--")
                plt.show()

                continue #value_list, grasp_list, stability_list = get_value_grasp_stability_lists(symmetry_activation_list)

            case "Sym_Act_Top":
                # success
                sym_act_success_list_top = sorted(sym_act_success_list[0:success_bound_indecies[0]], key = lambda x:(-x[2]))
                success_value_list, success_grasp_list, success_stability_list = get_value_grasp_stability_lists(sym_act_success_list_top)
                plot_median_with_deviations(success_stability_list, name="stable sym_act_top success")

                top_success_boundary_indecies = get_boundary_indecies(sym_act_success_list_top, val_grasp_stability_selection=2)
                sym_act_success_list_with_instable_top = sym_act_success_list_top[0:top_success_boundary_indecies[0]]
                sym_act_success_list_with_instable_mid = sym_act_success_list_top[top_success_boundary_indecies[1]:top_success_boundary_indecies[2]]
                sym_act_success_list_with_instable_bot = sym_act_success_list_top[top_success_boundary_indecies[3]:len(sym_act_success_list_top)]
                # failure
                sym_act_failure_list_top = sorted(sym_act_failure_list[0:failure_bound_indecies[0]], key = lambda x:(-x[2]))
                failure_value_list, failure_grasp_list, failure_stability_list = get_value_grasp_stability_lists(sym_act_failure_list_top)
                plot_median_with_deviations(failure_stability_list, name="stable sym_act_top failure")

                top_failure_boundary_indecies = get_boundary_indecies(sym_act_failure_list_top, val_grasp_stability_selection=2)
                sym_act_failure_list_with_instable_top = sym_act_failure_list_top[0:top_failure_boundary_indecies[0]]
                sym_act_failure_list_with_instable_mid = sym_act_failure_list_top[top_failure_boundary_indecies[1]:top_failure_boundary_indecies[2]]
                sym_act_failure_list_with_instable_bot = sym_act_failure_list_top[top_failure_boundary_indecies[3]:len(sym_act_failure_list_top)]
            case "Sym_Act_Mid":
                # success
                sym_act_success_list_mid = sorted(sym_act_success_list[success_bound_indecies[1]:success_bound_indecies[2]], key = lambda x:(-x[2]))
                success_value_list, success_grasp_list, success_stability_list = get_value_grasp_stability_lists(sym_act_success_list_mid)
                plot_median_with_deviations(success_stability_list, name="stable sym_act_mid success")

                mid_success_boundary_indecies = get_boundary_indecies(sym_act_success_list_mid, val_grasp_stability_selection=2)
                sym_act_success_list_with_instable_top = sym_act_success_list_mid[0:mid_success_boundary_indecies[0]]
                sym_act_success_list_with_instable_mid = sym_act_success_list_mid[mid_success_boundary_indecies[1]:mid_success_boundary_indecies[2]]
                sym_act_success_list_with_instable_bot = sym_act_success_list_mid[mid_success_boundary_indecies[3]:len(sym_act_success_list_mid)]
                # failure
                sym_act_failure_list_mid = sorted(sym_act_failure_list[failure_bound_indecies[1]:failure_bound_indecies[2]], key = lambda x:(-x[2]))
                failure_value_list, failure_grasp_list, failure_stability_list = get_value_grasp_stability_lists(sym_act_failure_list_mid)
                plot_median_with_deviations(failure_stability_list, name="stable sym_act_mid failure")

                mid_failure_boundary_indecies = get_boundary_indecies(sym_act_failure_list_mid, val_grasp_stability_selection=2)
                sym_act_failure_list_with_instable_top = sym_act_failure_list_mid[0:mid_failure_boundary_indecies[0]]
                sym_act_failure_list_with_instable_mid = sym_act_failure_list_mid[mid_failure_boundary_indecies[1]:mid_failure_boundary_indecies[2]]
                sym_act_failure_list_with_instable_bot = sym_act_failure_list_mid[mid_failure_boundary_indecies[3]:len(sym_act_failure_list_mid)]
            case "Sym_Act_Bot":
                # success
                sym_act_success_list_bot = sorted(sym_act_success_list[success_bound_indecies[3]:len(sym_act_success_list)], key = lambda x:(-x[2]))
                success_value_list, success_grasp_list, success_stability_list = get_value_grasp_stability_lists(sym_act_success_list_bot)
                plot_median_with_deviations(success_stability_list, name="stable sym_act_bot success")

                bot_success_boundary_indecies = get_boundary_indecies(sym_act_success_list_bot, val_grasp_stability_selection=2)
                sym_act_success_list_with_instable_top = sym_act_success_list_bot[0:bot_success_boundary_indecies[0]]
                sym_act_success_list_with_instable_mid = sym_act_success_list_bot[bot_success_boundary_indecies[1]:bot_success_boundary_indecies[2]]
                sym_act_success_list_with_instable_bot = sym_act_success_list_bot[bot_success_boundary_indecies[3]:len(sym_act_success_list_bot)]
                # failure
                sym_act_failure_list_bot = sorted(sym_act_failure_list[failure_bound_indecies[3]:len(sym_act_failure_list)], key = lambda x:(-x[2]))
                failure_value_list, failure_grasp_list, failure_stability_list = get_value_grasp_stability_lists(sym_act_failure_list_bot)
                plot_median_with_deviations(failure_stability_list, name="stable sym_act_bot failure")

                bot_failure_boundary_indecies = get_boundary_indecies(sym_act_failure_list_bot, val_grasp_stability_selection=2)
                sym_act_failure_list_with_instable_top = sym_act_failure_list_bot[0:bot_failure_boundary_indecies[0]]
                sym_act_failure_list_with_instable_mid = sym_act_failure_list_bot[bot_failure_boundary_indecies[1]:bot_failure_boundary_indecies[2]]
                sym_act_failure_list_with_instable_bot = sym_act_failure_list_bot[bot_failure_boundary_indecies[3]:len(sym_act_failure_list_bot)]
            case _:
                raise(Exception(f"Invalid Measure Used: {measure}"))

        # Save Successful Grasp info
        for i in range(len(success_grasp_list)):
            dir_list = str(success_grasp_list[i].data_path).split('/')
            # save to SUCCESS directory
            with open(str(save_directory / "SUCCESS" / f"Success_{file_name}"), 'a') as csv:
                csv.write(f"{success_value_list[i]},{success_grasp_list[i].grasp_outcome},{success_stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Save Failed Grasp info
        for i in range(len(failure_grasp_list)):
            dir_list = str(failure_grasp_list[i].data_path).split('/')
            # save to FAILURE directory
            with open(str(save_directory / "FAILURE" / f"Failure_{file_name}"), 'a') as csv:
                csv.write(f"{failure_value_list[i]},{failure_grasp_list[i].grasp_outcome},{failure_stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        ########################

        # Outcome: SUCCESS - Instability: TOP
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_success_list_with_instable_top)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "SUCCESS" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Success_Instable_Top_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Outcome: SUCCESS - Instability: MID
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_success_list_with_instable_mid)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "SUCCESS" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Success_Instable_Mid_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Outcome: SUCCESS - Instability: BOT
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_success_list_with_instable_bot)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "SUCCESS" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Success_Instable_Bot_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Outcome: FAILURE - Instability: TOP
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_failure_list_with_instable_top)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "FAILURE" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Failure_Instable_Top_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Outcome: FAILURE - Instability: MID
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_failure_list_with_instable_mid)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "FAILURE" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Failure_Instable_Mid_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")

        # Outcome: FAILURE - Instability: BOT
        value_list, grasp_list, stability_list = get_value_grasp_stability_lists(sym_act_failure_list_with_instable_bot)
        for i in range(len(grasp_list)):
            dir_list = str(grasp_list[i].data_path).split('/')
            # save to directory
            with open(str(save_directory / "FAILURE" / f"SYM_ACT_{measure.split('_')[-1].upper()}" / f"Failure_Instable_Bot_{file_name}"), 'a') as csv:
                csv.write(f"{value_list[i]},{grasp_list[i].grasp_outcome},{stability_list[i]},{dir_list[-7]},{dir_list[-6]},{dir_list[-5]},{dir_list[-4]},{dir_list[-3]},{dir_list[-2]},{dir_list[-1]},\n")


if(__name__ == "__main__"):
    main()