import pathlib
from input_handling import User_Selection
from sensors import Sensor_Reader
from actuators import Actuator_Actor

def main():
    # define folders paths needed for data gathering
    project_folder = pathlib.Path(__file__).parents[1]
    
    data_folder = project_folder / "Data"
    data_folder.mkdir(parents=True, exist_ok=True)



    # request descriptions for the grasp to the user
    print("BEGIN INITIALIZATION OF GRASP RECORDING...\n")
    selection = User_Selection(test=False)
    selection.prompt_all()



    sensor_reader = Sensor_Reader(
        use_tactile = False, 
        use_wrist_camera = False, 
        use_external_camera = True
    )

    actuator_actor = Actuator_Actor(
        use_claw = True
    )

    # Stage 0: Enter the closure diameter for the claw
    print("Gathering grasp parameters...")
    closure_amount = None
    while(closure_amount == None):
        try:
            user_input = input("Please select a closure diameter (0-18 cm) for this grasp: ")
            closure_amount = int(user_input)
        except:
            print("Invalid input, please try again...")
    actuator_actor.claw.set_claw_closure_diameter(diameter_cm=closure_amount)
    actuator_actor.claw.open()

    # Stage 1: Start the sensor recording
    print("\nReady to start grasp recording...")
    input("Press enter to continue.")
    print("\nStarting recording...")
    sensor_reader.start(user_selection=selection)
    print("Recording started!")

    # Stage 2: Close the claw when ready
    print("\nReady to start claw closure...")
    input("Press enter to continue.")
    actuator_actor.claw.close()

    # Stage 3: Stop the sensor recording
    print("\nReady to stop grasp recording...")
    input("Press enter to continue.")
    print("\nStopping recording...")
    sensor_reader.stop()
    print("Recording stopped!")

    # Stage 4: See if the grasp failed or succeeded
    print("Did the grasp Succeed or Fail?")
    print("\t0) Failed")
    print("\t1) Succeeded")
    success = None
    while(closure_amount == None):
        try:
            user_input = input("Please select a closure diameter (0-18 cm) for this grasp: ")
            succeeded = bool(int(user_input))
            path = pathlib.Path(__file__).parent
            with open(str(path / "grasp_condition.txt"), 'w') as file:
                if(succeeded):
                    file.write("SUCCESS")
                else:
                    file.write("FAILURE")
        except:
            print("Invalid input, please try again...")
    





# run only if file is executed directly
if(__name__ == "__main__"):
    main()