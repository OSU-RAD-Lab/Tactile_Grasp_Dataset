import socket
import struct
import threading

class Wireless_Claw():
    def __init__(self):
        print("Connecting to wireless Claw...")
        ARDUINO_IP = "192.168.8.216" 
        PORT = 10000

        self.claw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.claw_socket.connect((ARDUINO_IP, PORT))
        print("Claw connected!")

        self.closing_diameter_cm = 0
        self.open_diameter_cm = 18
        self.open_in_frame_diameter_cm = 15
        self.close_thread = threading.Thread(target=self.send_claw_command, args=(self.closing_diameter_cm,))
        self.open_thread = threading.Thread(target=self.send_claw_command, args=(self.open_diameter_cm,))
        self.open_in_frame_thread = threading.Thread(target=self.send_claw_command, args=(self.open_in_frame_diameter_cm,))

    def set_claw_closure_diameter(self, diameter_cm):
        self.closing_diameter_cm = diameter_cm
        self.close_thread = threading.Thread(target=self.send_claw_command, args=(self.closing_diameter_cm,))

    def close(self):
        print(f"Closing claw with closure diameter: {self.closing_diameter_cm} cm...")
        self.close_thread.start()
        self.close_thread = threading.Thread(target=self.send_claw_command, args=(self.closing_diameter_cm,))

    def open(self):
        print("Oening claw...")
        self.open_thread.start()
        self.open_thread.join()
        self.open_thread = threading.Thread(target=self.send_claw_command, args=(self.open_diameter_cm,))
        print("Claw open!")

        print("Setting claw in frame...")
        self.open_in_frame_thread.start()
        self.open_in_frame_thread.join()
        self.open_in_frame_thread = threading.Thread(target=self.send_claw_command, args=(self.open_in_frame_diameter_cm,))
        print("Claw set!")

    def send_claw_command(self, diameter):
            """
            speed: translates to delayMicroseconds on ESP32 (lower is faster)
            diameter: translates to steps_to_close on ESP32
            """
            try:
                with threading.Lock():
                    print(f"[CLAW] Sending claw command: closure_diameter={diameter}")

                    # pack into 1 char and 2 floats
                    # '<cff' = Little-endian, char, float, float
                    data = struct.pack('<ff', float(70.0), float(diameter))
                    self.claw_socket.sendall(data)
        
                # listen for data until you get a done message
                while True:
                    with threading.Lock():
                        response = self.claw_socket.recv(1024)
                        if response:
                            text = response.decode('utf-8').strip()
                            
                            # break when you get a done msg
                            if "DONE" in text:
                                # don't print done tho
                                text = text.replace("DONE", "").strip()
                                if text: 
                                    print(text)
                                break

                            else:
                                print(text)
                            
            except Exception as e:
                print(f"Error sending command: {e}")


class Actuator_Actor():
    def __init__(self, use_claw=True):
        self.use_claw = use_claw

        if(self.use_claw):
            self.claw = Wireless_Claw()
