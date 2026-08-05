import numpy as np
import time

N_BINS = 5 #TEST: 3, 5*, 10
P_ORDER = "PRE" #TEST: "PRE"*, "POST"
USE_ARTIFICIAL_NOISE = True #TEST: True, False
NOISE_LEVEL = 1/(2*N_BINS) # half of the first bin step will be the noise level
NOISE_PATTERN = "NOISE" #TEST: "NOISE", "PULSE", "WAVE"

class haptic_interpreter():
    def __init__(self):
        self.ANGLE_ZERO_PUSH = 180
        self.ANGLE_MAX_PUSH = 140
        self.ANGLE_DIFF_ZERO_TO_MAX_PUSH = self.ANGLE_MAX_PUSH - self.ANGLE_ZERO_PUSH

        self.DORSAL_HAPIC_ENHANCER = haptic_enhancer()
        #self.DORSAL_HAPIC_ENHANCER.set_rapid_adaptation(adaptation_rate=0.1)
        self.DORSAL_HAPIC_ENHANCER.set_P_controller(P=0.8, order=P_ORDER)
        self.DORSAL_HAPIC_ENHANCER.set_binning(num_bins=N_BINS)
        if(USE_ARTIFICIAL_NOISE):
            self.DORSAL_HAPIC_ENHANCER.set_artificial_noise(noise_level=NOISE_LEVEL, noise_pattern=NOISE_PATTERN)


        self.VOLAR_HAPIC_ENHANCER = haptic_enhancer()
        #self.VOLAR_HAPIC_ENHANCER.set_rapid_adaptation(adaptation_rate=0.1)
        self.VOLAR_HAPIC_ENHANCER.set_P_controller(P=0.8, order=P_ORDER)
        self.VOLAR_HAPIC_ENHANCER.set_binning(num_bins=N_BINS)
        if(USE_ARTIFICIAL_NOISE):
            self.VOLAR_HAPIC_ENHANCER.set_artificial_noise(noise_level=NOISE_LEVEL, noise_pattern=NOISE_PATTERN)

    def enhance_haptic_data(self, data):
        left_data = data[6::-1]
        right_data = data[13:6:-1]

        print(left_data)

        dorsal_row = [
            np.max([left_data[6], 0.5*left_data[5]]), # tip
            np.max([0.5*left_data[5], left_data[4], left_data[3], 0.5*left_data[2]]), # middle
            np.max([0.5*left_data[2], left_data[1], left_data[0]]) # base
        ]

        volar_row = [
            np.max([right_data[6], 0.5*right_data[5]]), # tip
            np.max([0.5*right_data[5], right_data[4], right_data[3], 0.5*right_data[2]]), # middle
            np.max([0.5*right_data[2], right_data[1], right_data[0]]) # base
        ]

        # apply haptic enhancers
        dorsal_row = self.DORSAL_HAPIC_ENHANCER.enhance(dorsal_row)
        volar_row = self.VOLAR_HAPIC_ENHANCER.enhance(volar_row)

        dorsal_row = self.ANGLE_ZERO_PUSH + self.ANGLE_DIFF_ZERO_TO_MAX_PUSH*np.array(dorsal_row)
        volar_row = self.ANGLE_ZERO_PUSH + self.ANGLE_DIFF_ZERO_TO_MAX_PUSH*np.array(volar_row)

        dorsal_row = dorsal_row.astype(int)
        volar_row = volar_row.astype(int)

        #print(dorsal_row)
        #print(volar_row)
        #print("---")

        return(dorsal_row, volar_row)
        

    def send_haptic_data(self, haptic_device, haptic_data):
        dorsal_row, volar_row = self.enhance_haptic_data(haptic_data)

        print("---")
        print(f"{dorsal_row[0]:.3f},{volar_row[0]:.3f}")
        print(f"{dorsal_row[1]:.3f},{volar_row[1]:.3f}")
        print(f"{dorsal_row[2]:.3f},{volar_row[2]:.3f}")
        print("---")
        # Haptic Device Ordering: Volar->Dorsal; Base->Tip
        serial_msg = f"[{volar_row[2]},{volar_row[1]},{volar_row[0]},{dorsal_row[2]},{dorsal_row[1]},{dorsal_row[0]}]"
        
        haptic_device.write(serial_msg.encode())

class haptic_enhancer():
    def __init__(self):
        self.prev_haptic_data = None

        self.use_binning = False
        self.num_bins = None

        self.use_P_controller = False
        self.P = None
        self.P_order = None

        self.use_rapid_adaptation = False
        self.adapted_point = None
        self.adaptation_rate = None

        self.use_artificial_noise = False
        self.noise_level = None
        self.noise_pattern = None
        self.active_pattern = None
        self.pattern_start_time = None
        self.last_pattern_poke = None
        

    def set_binning(self, num_bins):
        self.use_binning = True
        self.num_bins = num_bins

    def set_P_controller(self, P, order):
        self.use_P_controller = True
        self.prev_haptic_data = np.array([0.0, 0.0, 0.0])
        self.P = P
        if(order.upper() == "PRE" or order.upper() == "POST"):
            self.P_order = order.upper()
        else:
            raise(Exception("Incorrect Order Description Given for P Controller: must be PRE or POST"))

    def set_rapid_adaptation(self, adaptation_rate):
        self.use_rapid_adaptation = True
        self.adapted_point = np.array([0.0, 0.0, 0.0])
        self.adaptation_rate = adaptation_rate

    def set_artificial_noise(self, noise_level, noise_pattern):
        self.use_artificial_noise = True
        self.noise_level = noise_level
        self.noise_pattern = noise_pattern
        self.active_pattern = False
        self.pattern_start_time = time.time()
        self.last_pattern_poke = 0


    def enhance(self, haptic_data):
        enhanced_data = np.array(haptic_data)
        
        # subtract an adaptation point that is slowly changing to match the current haptic data
        if(self.use_rapid_adaptation):
            print("rapid-start")
            self.adapted_point = self.adaptation_rate*enhanced_data + (1-self.adaptation_rate)*self.adapted_point
            enhanced_data = enhanced_data - self.adapted_point + 0.5
            print(enhanced_data)
            # ensure the data does not go out of bounds
            for i in range(len(enhanced_data)):
                if(enhanced_data[i] > 1.0):
                    enhanced_data[i] = 1.0
                elif(enhanced_data[i] < 0.0):
                    enhanced_data[i] = 0.0
            print("rapid-end")

        # add a portion of the difference from the previous to current reading (i.e., error) to the new haptic reading
        if(self.use_P_controller and self.P_order == "PRE"):
            print("p-start")
            enhanced_data = self.prev_haptic_data + self.P*(enhanced_data - self.prev_haptic_data)
            # ensure the data does not go out of bounds
            for i in range(len(enhanced_data)):
                if(enhanced_data[i] > 1.0):
                    enhanced_data[i] = 1.0
                elif(enhanced_data[i] < 0.0):
                    enhanced_data[i] = 0.0
        
            # save the haptic data as the previous haptic data
            self.prev_haptic_data = enhanced_data
            print("p-end")

        # bin the data to not be continuous (more noticable jumps)
        if(self.use_binning):
            print("bin-start")
            enhanced_data = enhanced_data*self.num_bins + 0.5
            enhanced_data = enhanced_data.astype(int)
            enhanced_data = enhanced_data / self.num_bins
            print("bin-end")

        # add a portion of the difference from the previous to current reading (i.e., error) to the new haptic reading
        if(self.use_P_controller and self.P_order == "POST"):
            print("p-start")
            print(enhanced_data)
            enhanced_data = self.prev_haptic_data + self.P*(enhanced_data - self.prev_haptic_data)
            # ensure the data does not go out of bounds
            for i in range(len(enhanced_data)):
                if(enhanced_data[i] > 1.0):
                    enhanced_data[i] = 1.0
                elif(enhanced_data[i] < 0.0):
                    enhanced_data[i] = 0.0
        
            # save the haptic data as the previous haptic data
            self.prev_haptic_data = enhanced_data
            print("p-end")

        # add artificial noise to display to user that the device is on and waiting for contact
        if(self.use_artificial_noise):
            print("noise-start")
            # only add noise if there is no activation in any haptor
            if(np.sum(enhanced_data) <= self.noise_level):
                if(not self.active_pattern):
                    self.active_pattern = True
                    self.pattern_start_time = time.time()
                    self.last_pattern_poke = 0

                match(self.noise_pattern):
                    case "NOISE":
                        enhanced_data = self.noise_noise(enhanced_data)
                    case "PULSE":
                        enhanced_data = self.noise_pulse(enhanced_data)
                    case "WAVE":
                        enhanced_data = self.noise_wave(enhanced_data)
                        
            else:
                self.active_pattern = False
            print("noise-end")

        #return the enhanced data
        return(enhanced_data)
    
    def noise_noise(self, haptic_data):
        if(time.time() - self.pattern_start_time >= 0.5):
            for i in range(len(haptic_data)):
                haptic_data[i] = np.random.choice([0.0, 0.0, self.noise_level])
            self.pattern_start_time = time.time()
        return(haptic_data)
    
    def noise_pulse(self, haptic_data):
        if(time.time() - self.pattern_start_time >= 0.5):
            for i in range(len(haptic_data)):
                haptic_data[i] = self.noise_level
            self.pattern_start_time = time.time()
        return(haptic_data)
    
    def noise_wave(self, haptic_data):
        if(time.time() - self.pattern_start_time >= 0.2):
            haptic_data[self.last_pattern_poke] = self.noise_level
            self.last_pattern_poke += 1
            self.last_pattern_poke %= 3 # number of contact points on one side of haptic device
            self.pattern_start_time = time.time()
        return(haptic_data)
