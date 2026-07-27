import pathlib
from input_handling import User_Selection
from sensors import Sensor_Reader

def main():
    # define folders paths needed for data gathering
    project_folder = pathlib.Path(__file__).parents[1]
    
    data_folder = project_folder / "Data"
    data_folder.mkdir(parents=True, exist_ok=True)

    

    # request descriptions for the grasp to the user
    print("BEGIN INITIALIZATION OF GRASP RECORDING...\n")
    selection = User_Selection()
    selection.prompt_all()





# run only if file is executed directly
if(__name__ == "__main__"):
    main()