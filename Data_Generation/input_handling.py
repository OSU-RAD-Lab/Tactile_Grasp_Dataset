import pathlib
import time

class User_Selection():
    def __init__(self, test=False):
        # define the different dimensions of the grasp
        self.object_shape = None
        self.object_size = None
        self.object_material = None
        self.grasp_location = None
        self.grasp_eef_position = None
        self.grasp_interaction = None

        # specify if testing or not
        self.test = test

        # define the file path
        self.data_dir = pathlib.Path(__file__).parents[1] / "Data"
        self.dir_path = None
        self.unapplied_updates = True


    def selection_is_fully_specified(self):
        return(
            (self.object_shape is not None) and
            (self.object_size is not None) and
            (self.object_material is not None) and
            (self.grasp_location is not None) and
            (self.grasp_eef_position is not None) and
            (self.grasp_interaction is not None)
        )


    def prompt_select(self):
        while(True):
            print("\n==========")
            print("Please select the specification to change:")
            print("\t0) None (Finished)")
            print("\t1) Object Shape")
            print("\t2) Object Size")
            print("\t3) Object Material")
            print("\t4) Grasp Location")
            print("\t5) Grasp EEF Position")
            print("\t6) Grasp Interaction")
            print("==========")
            try:
                selection = int(input("Selection [0-6]:"))
            except:
                selection = -1
            print("==========\n")

            match(selection):
                case 0:
                    break
                case 1:
                    self.prompt_object_shape()
                case 2:
                    self.prompt_object_size()
                case 3:
                    self.prompt_object_material()
                case 4:
                    self.prompt_grasp_location()
                case 5:
                    self.prompt_grasp_eef_position()
                case 6:
                    self.prompt_grasp_interaction()
                case _:
                    print("\nERROR: Incorrect input. Please try again.\n")
                    continue


    def update_dir_path(self):
        # check if the user selection is fully specified
        if(not self.selection_is_fully_specified()):
            raise(Exception("ERROR: Selection is not fully specified!"))

        # find and create the directory if it doesnt already exist
        self.dir_path = self.data_dir / self.object_shape / self.object_size / self.object_material / self.grasp_interaction / self.grasp_location / self.grasp_eef_position
        if(self.test):
            self.dir_path = self.dir_path / "test"
        else:
            self.dir_path = self.dir_path / f"{time.time():.3f}"

        # create the path
        self.dir_path.mkdir(parents=True, exist_ok=True)
        self.unapplied_updates = False


    def get_dir_path(self):
        if(self.unapplied_updates):
            self.update_dir_path()

        return(self.dir_path)


    def print_user_selection(self):
        print("\n==========")
        print("The user currently has specified the following grasp:")
        print(f"\tObject Shape: {self.object_shape}")
        print(f"\tObject Size: {self.object_size}")
        print(f"\tObject Material: {self.object_material}")
        print(f"\tGrasp Location: {self.grasp_location}")
        print(f"\tGrasp EEF Position: {self.grasp_eef_position}")
        print(f"\tGrasp Interaction: {self.grasp_interaction}")
        print("==========\n")



    def prompt_all(self):
        """Prompt the user for each aspect of the grasp.\n- best for initial prompting or full selection reset"""

        # object prompts
        self.prompt_object_shape()
        self.prompt_object_size()
        self.prompt_object_material()
        # grasp prompts
        self.prompt_grasp_location()
        self.prompt_grasp_eef_position()
        self.prompt_grasp_interaction()



    def prompt_object_shape(self):
        self.unapplied_updates = True

        # reset object shape state
        self.object_shape = None

        # loop to ensure valid input
        while(self.object_shape is None):
            # prompt the user to select an object shape
            print("==========")
            print("Please select the SHAPE of the object being grasped")
            print("\t1) Asymmetrical Rectangle Prism")
            print("\t2) Cylinder")
            print("\t3) Plane")
            print("\t4) Ring")
            print("\t5) Sphere")
            print("\t6) Triangle Prism")
            print("==========")
            selection = input("Please select object shape [1-6]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.object_shape = "ASYM_RECT"
                    case 2:
                        self.object_shape = "CYLINDER"
                    case 3:
                        self.object_shape = "PLANE"
                    case 4:
                        self.object_shape = "RING"
                    case 5:
                        self.object_shape = "SPHERE"
                    case 6:
                        self.object_shape = "TRI_PRISM"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")



    def prompt_object_size(self):
        self.unapplied_updates = True

        # reset object size state
        self.object_size = None

        # loop to ensure valid input
        while(self.object_size is None):
            # prompt the user to select an object size
            print("==========")
            print("Please select the SIZE of the object being grasped")
            print("\t1) Small")
            print("\t2) Large")
            print("==========")
            selection = input("Please select object size [1-2]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.object_size = "SMALL"
                    case 2:
                        self.object_size = "LARGE"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")



    def prompt_object_material(self):
        self.unapplied_updates = True

        # reset object material state
        self.object_material = None

        # loop to ensure valid input
        while(self.object_material is None):
            # prompt the user to select an object material
            print("==========")
            print("Please select the MATERIAL of the object being grasped")
            print("\t1) Rigid")
            print("\t2) Compliant")
            print("==========")
            selection = input("Please select object material [1-2]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.object_material = "RIGID"
                    case 2:
                        self.object_material = "COMPLIANT"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")



    def prompt_grasp_location(self):
        self.unapplied_updates = True

        # reset grasp location state
        self.grasp_location = None

        # loop to ensure valid input
        while(self.grasp_location is None):
            # prompt the user to select an grasp location
            print("==========")
            print("Please select the LOCATION of the grasp")
            print("\t1) Top")
            print("\t2) Left")
            print("\t3) Front")
            print("\t4) Right")
            print("==========")
            selection = input("Please select grasp location [1-6]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.grasp_location = "TOP"
                    case 2:
                        self.grasp_location = "LEFT"
                    case 3:
                        self.grasp_location = "FRONT"
                    case 4:
                        self.grasp_location = "RIGHT"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")

    

    def prompt_grasp_eef_position(self):
        self.unapplied_updates = True

        # reset grasp end-effector position state
        self.grasp_eef_position = None

        # loop to ensure valid input
        while(self.grasp_eef_position is None):
            # prompt the user to select an grasp end-effector position
            print("==========")
            print("Please select the END-EFFECTOR POSITION of the grasp")
            print("\t1) Close")
            print("\t2) Center")
            print("\t3) Far")
            print("==========")
            selection = input("Please select grasp end-effector position [1-3]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.grasp_eef_position = "CLOSE"
                    case 2:
                        self.grasp_eef_position = "CENTER"
                    case 3:
                        self.grasp_eef_position = "FAR"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")



    def prompt_grasp_interaction(self):
        self.unapplied_updates = True

        # reset grasp interaction state
        self.grasp_interaction = None

        # loop to ensure valid input
        while(self.grasp_interaction is None):
            # prompt the user to select an grasp interaction
            print("==========")
            print("Please select the INTERACTION of the grasp")
            print("\t1) Free")
            print("\t2) Hook & Loop")
            print("\t3) String")
            print("==========")
            selection = input("Please select grasp interaction [1-3]: ")
            print("")

            # check for valid input
            try:
                # convert input to integer
                selection = int(selection)

                # see if the input matches possible selections
                match(selection):
                    case 1:
                        self.grasp_interaction = "FREE"
                    case 2:
                        self.grasp_interaction = "HOOK_AND_LOOP"
                    case 3:
                        self.grasp_interaction = "STRING"
                    case _:
                        raise(Exception("Invalid User Input"))
            
            # exception for any invalid input
            except:
                print("\nERROR: invalid input, please try again...\n")



# test the class
if(__name__ == "__main__"):
    # test class initiallization
    selection = User_Selection()
    
    # test object prompts
    selection.prompt_object_shape()
    selection.prompt_object_size()
    selection.prompt_object_material()

    # test specification check
    if(selection.selection_is_fully_specified()):
        print("Fully Specified Selection")
    else:
        print("WARNING: Selection Not Fully Specified")

    #test selection print
    selection.print_user_selection()

    # test grasp prompts
    selection.prompt_grasp_location()
    selection.prompt_grasp_eef_position()
    selection.prompt_grasp_interaction()

    # test specification check
    if(selection.selection_is_fully_specified()):
        print("Fully Specified Selection")
    else:
        print("WARNING: Selection Not Fully Specified")

    #test selection print
    selection.print_user_selection()