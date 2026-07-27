"""
Code modified from UVMS_ROS2_Interface Repo:
https://github.com/OSU-RAD-Lab/UVMS_ROS2_Interface/blob/main/UVMS_ws/src/robot_pkg/robot_pkg/sensors/tactile.py

Changes:
 - Removed ROS libraries
 - Changed ROS logs to python print statements
 - added start/stop recording functions
"""

import serial
from serial import Serial
import numpy as np
import time
import pathlib
import scipy.stats as Stats
import threading
import multiprocessing


"""
Initializes reader and interpreter
Read method will pull data, interpret it, and output a cleaned array
"""
class Tactile_Sensor():
    def __init__(self, tactile_name, port, baudrate=115200, num_taxels_per_sensor=7, num_sensors=2, read_method="hex", use_data_zeroing=False, use_data_smoothing=False, use_data_normalization=False, normalization_method="logistic"):
        # set the name of the tactile sensor
        self.tactile_name = tactile_name.replace(" ", "_")

        # Define a port for the sensor to read from
        self.port = port

        # Store sensor parameters
        self.use_data_zeroing = use_data_zeroing
        self.use_data_smoothing = use_data_smoothing
        self.use_data_normalization = use_data_normalization
        self.normalization_method = normalization_method

        # Specifiy variables for keeping track of tactile status
        self.last_read_success = None
        self.last_raw_readout = None
        self.last_interpret_readout = None

        # Define the tactile reader
        self.tactile_reader = Tactile_Reader(
            port = port,
            baudrate = baudrate,
            num_taxels_per_sensor = num_taxels_per_sensor,
            num_sensors = num_sensors,
            read_method = read_method
        )

        # Initiallize tactile status variables
        self.last_read_success = False
        self.last_raw_readout = np.array([0]*self.tactile_reader.data_len, dtype=np.float32)
        self.last_interpret_readout = np.array([0]*self.tactile_reader.data_len, dtype=np.float32)

        # Define a tactile interpreter
        self.tactile_interpreter = Tactile_Interpreter(
            use_data_zeroing = use_data_zeroing, 
            use_data_smoothing = use_data_smoothing, 
            use_data_normalization = use_data_normalization,
            normalization_method = normalization_method
        )

        self.read_period = 0.05
        self.recording = False
        self.calibrated = False


    def is_recording(self):
        return(self.recording)

    def is_calibrated(self):
        return(self.calibrated)

    def enable_recording(self):
        self.recording = True
    
    def disable_recording(self):
        self.recording = False
    
        

    def calibrate(self, calibration_readings=10):
        print(f"[{self.tactile_name}] Calibrating tactor...")
        # give some time to boot up
        time.sleep(3)
        if(self.tactile_reader.live_feed):
            # Gather readings from the tactile sensor
            tactile_readings = list()
            readings = 0
            while(readings < calibration_readings):
                # keep reading data until a tactile reading is successfully read
                success, tactile_reading = self.tactile_reader.read_tactile_sensor()
                self.last_read_success = success
                
                # append tactile data to list and keep track of is as most recent value read
                if(self.last_read_success):
                    self.last_raw_readout = tactile_reading
                    tactile_readings.append(self.last_raw_readout)
                    readings += 1
                    print(self.last_raw_readout)
                
                else:
                    print("[CALIBRATION] READING FAILED, TRYING AGAIN")
                
                # loop at the set period
                time.sleep(self.read_period)
            
        else:
            tactile_readings = np.loadtxt(
                str(self.port),
                skiprows = 1, 
                max_rows = 10,
                usecols = tuple(range(1,self.tactile_reader.data_len+1)),
                delimiter = ","
            )
            self.last_raw_readout = tactile_readings[-1]

        # Initiallize the tactile interpreter
        self.tactile_interpreter.compute_reference_readings(tactile_readings)
        self.tactile_interpreter.initiallize_sensor_buffer(tactile_readings, size=3)

        self.last_interpret_readout = self.tactile_interpreter.interpret_tactile_reading(self.last_raw_readout)

        self.calibrated = True
        print(f"[{self.tactile_name}] Tactor calibrated")


    def start(self):
        print(f"[{self.tactile_name}] Starting tactor...")
        if(self.is_recording()):
            print(f"[{self.tactile_name}] Tactor already started")
            return
        
        if(not self.is_calibrated()):
            print(f"[{self.tactile_name}] Tactor not calibrated...")
            self.calibrate()

        self.enable_recording()

        multiprocessing.Process
        self.tactile_recording_thread = threading.Thread(target=self.record, args=())
        self.tactile_recording_thread.start()
        #self.executor = ThreadPoolExecutor(max_workers=5)
        #self.executor.submit(self.record)


    def stop(self):
        with threading.Lock():
            self.disable_recording()


    def record(self):
        print(f"[{self.tactile_name}] Recording started @ {1/self.read_period:.2f} Hz")
        while(self.is_recording()):
            process_start_time = time.perf_counter()

            self.get_next_tactile_reading()
            if(not self.last_read_success):
                time.sleep(0.01)
                print(f"WARNING: Failed to read the {self.tactile_name} Tactile sensor (using last read value)")
                continue

            process_end_time = time.perf_counter()
            process_time = process_end_time - process_start_time
            remaining_time = self.read_period - process_time
            if(remaining_time >= 0):
                time.sleep(remaining_time)
            else:
                print(f"WARNING: {self.tactile_name} has a negative wait time for recording (skipping wait)")


    def get_next_tactile_reading(self):
        with threading.Lock():
            # Get the tactile reading
            success, tactile_reading = self.tactile_reader.read_tactile_sensor()
            self.last_read_success = success

            # Store the data if it was successful
            if(success):
                self.last_raw_readout = tactile_reading
                self.last_interpret_readout = self.tactile_interpreter.interpret_tactile_reading(self.last_raw_readout)
            else:
                return


    def read(self, output_raw_data):
        if(output_raw_data):
            return(self.last_raw_readout)
        else:
            return(self.last_interpret_readout)
        


"""
Takes raw data from tactile_reader and cleans it up 
"""
class Tactile_Interpreter():
    def __init__(self, use_data_zeroing=False, use_data_smoothing=False, use_data_normalization=False, normalization_method="split_logistic"):
        # save the option of having data zeroed or not
        self.use_data_zeroing = use_data_zeroing
        # save the option of having data smoothing or not
        self.use_data_smoothing = use_data_smoothing
        # save option for having data normalized or not
        self.use_data_normalization = use_data_normalization
        self.normalization_method = normalization_method # can be: [logisitc-sigma-offset] or [min_step_logistic-num_below-num_above]

        # Specify the reference values for the zero-force readings
        self.median_values_zero_force = None
        self.mean_values_zero_force = None
        self.std_values_zero_force = None
        
        # Specify the sensor buffer variables to use when smoothing the data
        self.sensor_buffer = None
        self.buffer_counter = None


    def initiallize(self, zero_force_tactile_readings_list, num_readings=None, size=None):
        # Get the number of tactile readings in the passed array
        num_tactile_readings = len(zero_force_tactile_readings_list)
        # check if any parameters provided to override default
        if(num_readings is None):
            num_readings = num_tactile_readings
        if(size is None):
            size = num_tactile_readings
        
        # use the passed data to compute the reference values
        self.compute_reference_readings(zero_force_tactile_readings_list, num_readings=num_readings)
        
        # Gather the interpreted values (without smoothing) passed data
        interpreted_reference_values = list()
        for tactile_reading in zero_force_tactile_readings_list:
            interpreted_tactile_reading = self.interpret_tactile_reading(tactile_reading, use_data_smoothing=False)
            interpreted_reference_values.append(interpreted_tactile_reading)
        # Use the interpreted data to initiallize the sensor buffer
        interpreted_reference_values = np.array(interpreted_reference_values)
        self.initiallize_sensor_buffer(interpreted_reference_values, size=size)


    def compute_reference_readings(self, zero_force_tactile_readings_list, num_readings=None):
        # get a subset of the tactile readings if a value is specified
        if(not (num_readings is None)):
            # check to ensure the number of readings is not more than are in the list provided
            list_length = len(zero_force_tactile_readings_list)
            if(list_length < num_readings):
                raise(Exception("Error: specified list length is longer than number of tactile readings in list"))
            # Get the subset of the tactile readings
            zero_force_tactile_readings_list = zero_force_tactile_readings_list[0:num_readings]
        # convert the list of reference tactile readings to a numpy array
        zero_force_reference_readings = np.array(zero_force_tactile_readings_list, dtype=np.float32)
        # compute the median, mean, and std of each taxel
        self.median_values_zero_force = np.median(zero_force_reference_readings, axis=0).astype(dtype=np.float32)
        self.mean_values_zero_force = np.mean(zero_force_reference_readings, axis=0).astype(dtype=np.float32)

        self.mad_values_zero_force = Stats.median_abs_deviation(zero_force_reference_readings, axis=0).astype(dtype=np.float32)
        self.std_values_zero_force = np.std(zero_force_reference_readings, axis=0).astype(dtype=np.float32)

        self.mad_values_zero_force[self.mad_values_zero_force==0] = 1.0
        self.std_values_zero_force[self.std_values_zero_force==0] = 1.0

        # offset the mean if data zeroing is active (std remains the same)
        if(self.use_data_zeroing):
            self.mean_values_zero_force -= self.median_values_zero_force


    def initiallize_sensor_buffer(self, tactile_readings_list, size=None):
        # get a subset of the tactile readings if a value is specified
        if(not (size is None)):
            # check to ensure the number of readings is not more than are in the list provided
            list_length = len(tactile_readings_list)
            if(list_length < size):
                raise(Exception("Error: specified list length is longer than number of tactile readings in list"))
            # Get the subset of the tactile readings (the most recent instances)
            tactile_readings_list = tactile_readings_list[(list_length-size):list_length]
        # Make the sensor buffer (and counter) a list of tactile readngs provided
        self.sensor_buffer = np.array(tactile_readings_list, dtype=np.float32)
        self.buffer_counter = 0


    def interpret_tactile_reading(self, tactile_reading, use_data_zeroing=None, use_data_smoothing=None, use_data_normalization=None, normalization_method=None):
        # Check for any parameters added to override class variables
        if(use_data_zeroing is None):
            use_data_zeroing = self.use_data_zeroing
        if(use_data_smoothing is None):
            use_data_smoothing = self.use_data_smoothing
        if(use_data_normalization is None):
            use_data_normalization = self.use_data_normalization
        if(normalization_method is None):
            normalization_method = self.normalization_method
        
        # Ensure that the tactile reading is a numpy array
        tactile_reading = np.array(tactile_reading, dtype=np.float32)

        # Zero the data of needed
        if(use_data_zeroing):
            tactile_reading = self._data_zero_reading(tactile_reading)
        
        # Smooth the data if needed
        if(use_data_smoothing):
            tactile_reading = self._data_smooth_reading(tactile_reading)

        # Normalize the data if needed
        if(use_data_normalization):
            tactile_reading = self._data_normalize_reading(tactile_reading, normalization_method=normalization_method)

        # Return the modified tactile reading
        return(tactile_reading)


    def _data_zero_reading(self, tactile_reading):
        # Subtract the reference median value from each sensor to zero it based on the median
        tactile_reading -= self.median_values_zero_force
        # Return the modified tactile reading
        return(tactile_reading)
    

    def _data_smooth_reading(self, tactile_reading):
        # Add the tactile reading to the sensor buffer
        self.sensor_buffer[self.buffer_counter, :] = tactile_reading
        self.buffer_counter += 1
        self.buffer_counter %= len(self.sensor_buffer)
        # Get the median value of the sensor buffer
        tactile_reading = np.median(self.sensor_buffer, axis=0)
        # Return the modified tactile reading
        return(tactile_reading)
    

    def _compute_robust_z_score(self, x):
        robust_z_score = 0.6745*(x - self.median_values_zero_force) / self.mad_values_zero_force
        return(robust_z_score)
    
    def _compute_z_score(self, x):
        z_score = (x - self.mean_values_zero_force) / self.std_values_zero_force
        return(z_score)


    def _data_normalize_reading(self, tactile_reading, normalization_method):
        normalization_info = normalization_method.replace(" ", "").upper().split(";")
        scaling_info = normalization_info[0].split('.')
        if(len(scaling_info) == 2):
            normalization_method = scaling_info[0]
            vacuum_info = scaling_info[1]
        else:
            #print("[TACTILE] WARNING: Using Default Vacuum Info (VAC_0-1-SCALE) for Normalization Method")
            normalization_method = normalization_info[0]
            vacuum_info = "VAC_0-1-SCALE"

        match(normalization_method):
            case "FOR_HAPTIC_DEVICE":
                # get z scores 
                tactile_z_score = self._compute_z_score(tactile_reading)
                # get rid of negative and account for smaller negative values with side forces
                tactile_z_score[tactile_z_score < 0] = np.pow(tactile_z_score[tactile_z_score < 0], 2)
                # Normalize tactile readings
                normalized_tactile_readings = 1/(1 + np.exp(3 - 0.09*tactile_z_score))
                

            case "Z_POW":
                # gather normalization case information
                if(len(normalization_info) != 4):
                    pow = 1
                    lower_z = 0
                    upper_z = 2
                else:
                    pow = float(normalization_info[1])
                    lower_z = float(normalization_info[2])
                    upper_z = float(normalization_info[3])
                # define boundary baased on power to the min and max z value
                lower_bound = (lower_z/np.abs(lower_z))*np.power(abs(lower_z), pow)
                upper_bound = (upper_z/np.abs(upper_z))*np.power(abs(upper_z), pow)
                # get the z value of the tactile sensor and 
                tactile_reading_z = (tactile_reading - self.mean_values_zero_force)/self.std_values_zero_force
                sign_z = 2*(tactile_reading_z > 0) - 1
                tactile_reading_z_pow = sign_z*np.power(np.abs(tactile_reading_z), pow)
                # apply the boundaries
                tactile_reading_z_pow[tactile_reading_z_pow < lower_bound] = lower_bound
                tactile_reading_z_pow[tactile_reading_z_pow > upper_bound] = upper_bound
                # normalize the powered Z-values based on the defined boundaries
                tactile_reading_z_pow -= lower_bound
                tactile_reading_z_pow /= (upper_bound - lower_bound)
                # save the normallized tactile reading
                normalized_tactile_readings = tactile_reading_z_pow

            case "LOGISTIC":
                # gather normalization case information
                if(len(normalization_info) != 3):
                    sigma = 1
                    offset = 0
                else:
                    sigma = float(normalization_info[1])
                    offset = float(normalization_info[2])
                # Get the z-value for the tactile readings
                tactile_reading_z = (tactile_reading - self.mean_values_zero_force)/self.std_values_zero_force
                # apply the logistic function on the z values
                normalized_tactile_readings = 1.0/(1.0 + np.exp(-sigma*tactile_reading_z - offset))
            
            case "SPLIT_LOGISTIC":
                # have p=0.5 for range of values and continue the logistic logistic-horizontal-logistic
                # gather normalization case information
                if(len(normalization_info) != 3):
                    sigma = 1
                    z_split = 2
                else:
                    sigma = float(normalization_info[1])
                    z_split = float(normalization_info[2])
                # Get the z-value for the tactile readings
                tactile_reading_z = (tactile_reading - self.mean_values_zero_force)/self.std_values_zero_force
                # apply the logistic function on the z values
                tactile_reading_z[np.abs(tactile_reading_z) < z_split] = 0.5
                tactile_reading_z[tactile_reading_z < -z_split] = 1.0/(1.0 + np.exp(-sigma*(tactile_reading_z[tactile_reading_z < -z_split] + z_split)))
                tactile_reading_z[tactile_reading_z > z_split] = 1.0/(1.0 + np.exp(-sigma*(tactile_reading_z[tactile_reading_z > z_split] - z_split)))
                # save the normallized tactile reading
                normalized_tactile_readings = tactile_reading_z
                
            case "MIN_STEP_LOGISTIC":
                # gather normalization case information
                if(len(normalization_info) != 3):
                    num_lower_groups = 0
                    num_higher_groups = 1
                else:
                    num_lower_groups = int(normalization_info[1])
                    num_higher_groups = int(normalization_info[2])
                # normalize the data using the min step logistic
                tactile_reading = self._data_normalize_reading_min_step_logistic(
                    tactile_reading, 
                    num_lower_groups = num_lower_groups,
                    num_higher_groups = num_higher_groups
                )
                # save the normallized tactile reading
                normalized_tactile_readings = tactile_reading
            
            case _:
                # DEFAULT CASE
                print("[TACTILE] WARNING: Using Default Normalization Case")
                # normalize the values based on the percentage of the reading they take
                tactile_reading = tactile_reading / np.sum(tactile_reading)
                # save the normallized tactile reading
                normalized_tactile_readings = tactile_reading
            
        match(vacuum_info):
            case "VAC":
                normalized_tactile_readings = 2*normalized_tactile_readings - 1

            case "VAC_CUTOFF":
                normalized_tactile_readings = 2*normalized_tactile_readings - 1
                normalized_tactile_readings[normalized_tactile_readings < 0] = 0.0
            
            case "VAC_STATE-SHIFT":
                normalized_tactile_readings = 2*normalized_tactile_readings - 1
                normalized_tactile_readings[normalized_tactile_readings < 0] = -0.5*normalized_tactile_readings[normalized_tactile_readings < 0]
            
            case "VAC_0-1-SCALE":
                # default of the normalization computation, no additional computation needed
                pass
            
            case "VAC_ABS":
                normalized_tactile_readings = 2*normalized_tactile_readings - 1
                normalized_tactile_readings = np.abs(normalized_tactile_readings)

            case _:
                # DEFAULT CASE
                print("[TACTILE] WARNING: Using Default Vacuum information case")
                pass
        # return the normallized tactile information
        return(normalized_tactile_readings)

    
    def _data_normalize_reading_min_step_logistic(self, tactile_reading, num_lower_groups, num_higher_groups):
        # Vectorize the function to compute values in parallel
        min_step_normalizer_function = np.vectorize(self._min_step_normalize_reading)
        # Use the vectorized normalizer function
        tactile_reading = min_step_normalizer_function(
            tactile_reading, 
            # parameters related to the steps
            num_lower_groups = num_lower_groups, 
            num_higher_groups = num_higher_groups,
            # parameters related to the distribution
            mean_zero_force = self.mean_values_zero_force, 
            std_zero_force = self.std_values_zero_force, 
            significant_num_std = 2.5
        )
        # Return the modified tactile reading
        return(tactile_reading)


    def _min_step_normalize_reading(self, tactile_reading, num_lower_groups, num_higher_groups, mean_zero_force=0, std_zero_force=1, significant_num_std=2):
        # ===============================================
        # ===============================================
        # ### Overly complicated: will need to change ###
        # ## Maybe have separate functions to try out! ##
        # ===============================================
        # ===============================================

        # check for valid number of groups
        total_groups = num_lower_groups + 1 + num_higher_groups
        if(total_groups < 2):
            raise(Exception("Invalid number of groupings for the normalizer"))

        # Get the z value and group of the reading        
        z = (tactile_reading - mean_zero_force) / (std_zero_force)
        group = (z // (2*significant_num_std)) + 1

        # Bound the group depending on the total number of higher/lower groups available
        if(group < -num_lower_groups + 1):
            group = -num_lower_groups + 1
        elif(group > num_higher_groups):
            group = num_higher_groups

        # Determine how to scale the logistic curves based on the total number logistics available
        num_logistic_curves = total_groups - 1
        scale_factor = 1/(num_logistic_curves)

        # Get the lower bound based on the current group for the reading and the total number of logistic curves
        logistic_index = group + num_lower_groups - 1
        lower_bound = (logistic_index*scale_factor)

        # Get the probability of being in the higher distribution for current reading and the current group number
        k = 2*significant_num_std*(z - (2*group-1)*significant_num_std)
        prob = 1 / (1 + np.exp(-k))
        
        # Scale the probability to fit in the bounds of the current group (i.e., the value for the percent activation)
        activation = scale_factor*prob + lower_bound
        
        # return the activation
        return(activation)


"""
This class fetches raw data
Given a serial port, it reads live data from the port
"""
class Tactile_Reader():
    def __init__(self, port, baudrate=115200, num_taxels_per_sensor=7, num_sensors=2, read_method="hex"):
        # Defining sensor object
        print("[TACTILE] Defining tactile reader...")

        # save the tactile port
        self.port = port
        # save the baudrate
        self.baudrate = baudrate
        # Length of data stream from microcontroller
        self.data_len = num_taxels_per_sensor * num_sensors
        # save the method to use when reading tactile data
        self.read_method = read_method

        # Determine if the tactile reader is getting live or recorded data from the port
        self._infer_port()
        
        # specify variables for the tactile reader status
        self.prev_datapoint_index = None

        # Define a tactile reader on live data
        if(self.live_feed):
            # Establish serial communication
            self.tactile_reader, self.data_timing = self._establish_serial_communication()
            # Start the serial communication
            self.connected = self._start_serial_communication()
            # Check if serial communication was actually achieved
            if(not self.connected):
                raise Exception("[TACTILE] Problem with starting serial communication! Please try again...")
            else:
                print("[TACTILE] Serial communication established!")
        
        # Define a tactile reader on pre-recorded data
        else:
            # Open the tactile datafile for the recorded data
            self.tactile_reader, self.data_timing = self._open_tactile_datafile()
            self.prev_datapoint_index = -1
        
        # time delay to ensure stable setup
        time.sleep(3)
    
    def __del__(self):
        # only needed if there was a live feed
        if(self.live_feed):
            # Close serial communication
            try:
                self.tactile_reader.close()
            except:
                print("Attempted to close serial port in destructor that resulted in an exception (bypassing exception)")

    def read_tactile_sensor(self, read_method_override=None):
        # Decide to use local or class value
        read_method = self.read_method
        if(read_method_override is not None):
            read_method = read_method_override
        
        #reset the buffers to get the newest data point before reading
        if(self.live_feed):
            self.tactile_reader.reset_input_buffer()
        
        # call the specified tactile reading method to gather the data
        match(read_method.upper()):
            case "PRINT":
                is_success, reading = self._read_tactile_sensor_print()
                self.tactile_reader.reset_input_buffer()
                self.tactile_reader.reset_output_buffer()
            case "HEX":
                is_success, reading = self._read_tactile_sensor_hex()
                self.tactile_reader.reset_input_buffer()
                self.tactile_reader.reset_output_buffer()
            case "BIN":
                is_success, reading = self._read_tactile_sensor_bin()
                self.tactile_reader.reset_input_buffer()
                self.tactile_reader.reset_output_buffer()
            case "FILE":
                is_success, reading = self._read_tactile_sensor_file()
        
        # return whether the reading was successful and the value recieved
        return(is_success, reading)
    

    def _read_tactile_sensor_print(self):
        msg = ""
        b = str(self.tactile_reader.read(1).decode())
        while (b != '\n'):
            msg += b
            b = str(self.tactile_reader.read(1).decode())

        msg = msg.split(';')
        return msg[0:len(msg)-1]


    def _read_tactile_sensor_hex(self):
        b = str(self.tactile_reader.read(1).decode())
        msg = ""
        while (b != '\n'):
            msg += b
            while(self.tactile_reader.inWaiting() == 0):
                time.sleep(0.001)
            b = str(self.tactile_reader.read(1).decode())
        
        msg = msg.split(';')

        if(len(msg) != self.data_len+1):
            print(f"[TACTILE] ERROR: Got {msg}")
            is_success = False
            data = None
            return(is_success, data)
        
        hex_list = list()
        for hex_string in msg[0:len(msg)-1]:
            if(hex_string == ''):
                print(f"[TACTILE] VALUE ERROR: In {msg}")
                is_success = False
                data = None
                return(is_success, data)
            hex_val = int(hex_string, 16)
            hex_list.append(hex_val)
        
        is_success = True
        hex_array = np.array(hex_list, dtype=np.float32)
        return(is_success, hex_array)


    def _read_tactile_sensor_bin(self):
        val_list = list()
        for i in range(self.data_len):
            msg = 0
            b = int.from_bytes(self.tactile_reader.read(1),'big')
            byteArray = [b]

            while ((b >> 7) & 1):
                b = int.from_bytes(self.tactile_reader.read(1),'big')
                byteArray.append(b)

            for i, byte in enumerate(reversed(byteArray)):
                byte = byte & ~(1<<7)
                msg = msg | (byte << (i*7))
            if msg > 50000:
                msg = msg - 65536

            val_list.append(msg)

        return val_list
    

    def _read_tactile_sensor_file(self):
        #
        passed_time_ms = int(time.time()*1000)
        data_number = np.sum(self.data_timing <= passed_time_ms) - 1
        if(data_number < 0):
            data_number = 0
        #
        if(data_number == self.prev_datapoint_index):
            is_success = False
            tactile_data = None
        #
        else:
            is_success = True
            self.prev_datapoint_index = data_number
            tactile_data = np.array(self.tactile_reader[data_number, :], dtype=np.float32)
        #
        return(is_success, tactile_data)
    

    def _start_serial_communication(self, timeout=5):
        # Write an initial bit to the microcontroller to initiate serial communication
        try:
            self.tactile_reader.write(b'a')
        except serial.serialutil.SerialTimeoutException:
            print("[TACTILE] Write timeout reached! Skipping sending initial bit")
        # get the starting time and timeout to wait for acknowledgement bit
        send_time = time.time()
        # flag indicating return character received
        start_byte_received = False
        # wait for return byte, stop trying if exceed timeout
        while((not start_byte_received) and ((time.time() - send_time) < timeout)):
            b = int.from_bytes(self.tactile_reader.read(1),'big')
            print(f"[TACTILE] {b}")
            if b != 0:
                start_byte_received = True
            else:
                self.tactile_reader.reset_input_buffer()
                self.tactile_reader.reset_output_buffer()
            time.sleep(0.1)
        # return status of acknowledgement bit
        return start_byte_received
    

    def _infer_port(self, port=None):
        # Determine if port is to be used from the class or as defined from the function
        if(port is None):
            port = self.port
        # Determine if the tactile reader is getting live or recorded data
        # Case for reading recorded data (path given for port)
        if(isinstance(port, pathlib.Path)):
            self.read_method = "file"
            self.live_feed = False
        # Case for reading live data from Windows machine (string given for port)
        elif(isinstance(port, str)):
            self.live_feed = True
        # Case for reading live data from Linux machine (int given for port)
        elif(isinstance(port, int)):
            self.port = f"/dev/ttyACM{port}"
            self.live_feed = True
        else:
            raise(Exception("Invalid port number! Use either String for Windows COM or an integer for Linux (do not specify ttyACM path)"))
        

    def _establish_serial_communication(self):
        print(f"[TACTILE] Establishing serial communication (port: {self.port}, baud: {self.baudrate})...")
        tactile_reader = Serial(
            port = self.port,
            baudrate = self.baudrate,
            dsrdtr = False,
            timeout = 1,
            write_timeout = 1
        )
        # Timeout to allow the serial connection to stabilize
        time.sleep(3)
        # clear any data on the buffer
        tactile_reader.reset_input_buffer()
        tactile_reader.reset_output_buffer()
        # No timing needed when reading live data
        data_timing = None
        return(tactile_reader, data_timing)
    

    def _open_tactile_datafile(self):
        print("[TACTILE] Opening Tactile datafile...")
        tactile_reader = np.genfromtxt(str(self.port), delimiter=',', dtype=np.float32, skip_header=1, skip_footer=1)
        print("[TACTILE] Tactile datafile opened!")
        print("[TACTILE] Formatting tactile data...")
        data_timing = tactile_reader[:, 0].flatten()
        tactile_reader = tactile_reader[:, 1:len(tactile_reader[0,:])-1]
        print("[TACTILE] Tactile data formatted!")
        return(tactile_reader, data_timing)
    



if(__name__ == "__main__"):
    # test the tactile sensor object
    tactile_sensor = Tactile_Sensor(
        tactile_name = "test_tactor",
        port = "/dev/ttyACM0", 
        use_data_zeroing = False, #normalization will account for zeroing
        use_data_smoothing = True, 
        use_data_normalization = False, 
        normalization_method = "FOR_HAPTIC_DEVICE" 
    )
    
    tactile_sensor.calibrate(calibration_readings=100)
    tactile_sensor.start()
    
    start_time = time.time()
    count = 0
    while(time.time()-start_time < 10):
        count += 1
        tactor_data = tactile_sensor.read(output_raw_data=True)
        print(tactor_data)
        time.sleep(tactile_sensor.read_period)
    print(count)
    tactile_sensor.stop()
    
