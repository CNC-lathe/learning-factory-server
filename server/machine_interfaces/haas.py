# Luke Minton, MDE Fall 2021, VT ISE Learning Factory, Interface from Haas CNC machine to LF server
# Machine currently has a serial (RS232) to USB port

import serial, time, sys, zmq, pickle
from typing import Dict, Any
from threading import Thread
from base import MachineInterface
from lf_utils import retry

# Haas macros for pulling data
COOLANT_LEVEL = b"?Q600 1094\r\n"
SPINDLE_SPEED = b"?Q600 3027\r\n"
MACHINE_COORD_X = b"?Q600 5021\r\n"
MACHINE_COORD_Y = b"?Q600 5022\r\n"
MACHINE_COORD_Z = b"?Q600 5023\r\n"
MACHINE_COORD_A = b"?Q600 5024\r\n"
MACHINE_COORD_B = b"?Q600 5025\r\n"
WORK_COORD_X = b"?Q600 5041\r\n"
WORK_COORD_Y = b"?Q600 5042\r\n"
WORK_COORD_Z = b"?Q600 5043\r\n"
WORK_COORD_A = b"?Q600 5044\r\n"
WORK_COORD_B = b"?Q600 5045\r\n"

# Inherit from the Machine Interface class defined in base.py
class HaasInterface(MachineInterface):
    
    def __init__(self, publish_port: int, machine_config: Dict, serial_port: str):

        # set machine config
        self._machine_config = machine_config

        # set serial port name (i.e. COM3)
        self._serial_port = serial.Serial(port = serial_port, baudrate = 9600, bytesize = serial.SEVENBITS, xonxoff = True, timeout = 5)

        # Attempt to open a serial port for communication with the Haas
        try:
            self._serial_port.open()
        except serial.SerialException:
            if self._serial_port.is_open:
                try:
                    print("Port was open, attempting to close and reopen")
                    self._serial_port.close()
                    time.sleep(2)
                    self._serial_port.open()
                except:
                    print("Failed to close port")
                    event.clear()
            else:
                print("Failed to connect to serial port, either in use or does not exist")
                event.clear() 

        # set machine name
        self._machine_name = self._machine_config["Haas CNC"]

        # set up publish address
        self._publish_address = f"tcp://127.0.0.1:{publish_port}"

        # set up publish socket
        self._context = zmq.Context()
        self._publish_socket = self._context.socket(zmq.PUB)
        retry(
            self._publish_socket.connect,
            self._publish_address,
            handled_exceptions=zmq.error.ZMQError
        )

        # initialize thread
        Thread.__init__(self)
        self._stopped = False

    def run(self):
        # loop until thread is stopped
        while not self._stopped:
            # get machine data
            machine_data = self._poll_machine()

            # publish machine data
            self._publish_data(self._publish_socket, self._machine_name, machine_data)

        # close ZMQ socket and context
        self._close_zmq()

    def stop(self):
        self._stopped = True

    # Redefine abstract method to poll a machine for data
    def _poll_machine(self):

        # Helper function to get write macros to Haas requesting specific data
        def get_data(ser, constant, output):
            try:
                ser.write(constant)
                while True:
                    output = ser.readline().decode("utf-8")
                    if len(output) > 4:
                        break
                output = output.split(",")[2].strip()[0:8]
            except:
                output = '0'
            return output

        print("Begin data collection:")

        # Begin fetching data from Haas (comment out while loop for one-time testing)
        while True:
            try:
                # Coolant Level Data
                coolant_lvl = ''
                coolant_lvl = get_data(self._serial_port, COOLANT_LEVEL, coolant_lvl)
                self._machine_config['Coolant Level'] = coolant_lvl
                print("Coolant level: " + coolant_lvl)

                # Spindle Speed RPM
                spindle_spd = ''
                spindle_spd = get_data(self._serial_port, SPINDLE_SPEED, spindle_spd)
                self._machine_config['Spindle Speed'] = spindle_spd
                print("Spindle speed: " + spindle_spd)

                # Machine Coords (X, Y, Z, A, B)
                machine_x = ''
                machine_x = get_data(self._serial_port, MACHINE_COORD_X, machine_x)
                self._machine_config['Machine Coordinate X Value'] = machine_x
                print("Machine coordinate X: " + machine_x)

                machine_y = ''
                machine_y = get_data(self._serial_port, MACHINE_COORD_Y, machine_y)
                self._machine_config['Machine Coordinate Y Value'] = machine_y
                print("Machine coordinate Y: " + machine_y)

                machine_z = ''
                machine_z = get_data(self._serial_port, MACHINE_COORD_Z, machine_z)
                self._machine_config['Machine Coordinate Z Value'] = machine_z
                print("Machine coordinate Z: " + machine_z)

                machine_a = ''
                machine_a = get_data(self._serial_port, MACHINE_COORD_A, machine_a)
                self._machine_config['Machine Coordinate A Value'] = machine_a
                print("Machine coordinate A: " + machine_a)

                machine_b = ''
                machine_b = get_data(self._serial_port, MACHINE_COORD_B, machine_b)
                self._machine_config['Machine Coordinate B Value'] = machine_b
                print("Machine coodinate B: " + machine_b)

                # Work Coords (X, Y, Z, A, B)
                work_x = ''
                work_x = get_data(self._serial_port, WORK_COORD_X, work_x)
                self._machine_config['Work Coordinate X Value'] = work_x
                print("Work coordinate X: " + work_x)

                work_y = ''
                work_y = get_data(self._serial_port, WORK_COORD_Y, work_y)
                self._machine_config['Work Coordinate Y Value'] = work_y
                print("Work coordinate Y: " + work_y)

                work_z = ''
                work_z = get_data(self._serial_port, WORK_COORD_Z, work_z)
                self._machine_config['Work Coordinate Z Value'] = work_z
                print("Work coordinate Z: " + work_z)

                work_a = ''
                work_a = get_data(self._serial_port, WORK_COORD_A, work_a)
                self._machine_config['Work Coordinate A Value'] = work_a
                print("Work coordinate A: " + work_a)

                work_b = ''
                work_b = get_data(self._serial_port, WORK_COORD_B, work_b)
                self._machine_config['Work Coordinate B Value'] = work_b
                print("Work coordinate B: " + work_b)

            except Exception as ex:
                print("Failed to retrive any data from machine" + str(ex))
                time.sleep(2)
    
        self._serial_port.close()

        # Return the dictionary of data
        return self._machine_config
    
    @staticmethod
    def _publish_data(publish_socket: zmq.Socket, machine_name: str, machine_data: Dict[str, Any]):
        
        publish_socket.send_multipart([bytes(machine_name, "utf-8"), pickle.dumps(machine_data)])

    def _close_zmq(self):
        # destroy context
        self._context.destroy()
        