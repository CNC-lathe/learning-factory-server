# Luke Minton, MDE Fall 2021, VT ISE Learning Factory, Interface from Haas CNC machine to LF server
# Machine currently has a serial (RS232) to USB port

import serial, time, sys, zmq, pickle, yaml
from typing import Dict, Any
from threading import Thread
from base import MachineInterface
from lf_utils import retry
import lf_utils.yaml_loader


# Inherit from the Machine Interface class defined in base.py
class HaasInterface(MachineInterface):
    """Defines Haas Interface Class"""
    def __init__(self, publish_port: int, machine_config: Dict, serial_port: str):
        """Intializes the Haas CNC hardware interface, publish port, and serial port

        Parameters
        ----------
        publish_port : Optional[int]
            port to publish data to
        machine_config : Dict
            Haas interface configuration dictionary
        serial_port : str
            serial port to send data to (typically a COM port)
        """
        # Inherit methods from the base class
        super.__init__()

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

    @staticmethod
    def get_data(ser, constant):
        """Helper function for writing defined macros to the Haas

        Parameters
        ----------
        ser : str
            serial port to send macros to and recieve data from the Haas
        constant : str
            predefined macros to request desired data from the Haas

        Returns
        -------
        str
            parsed machine data returned directly from the Haas
        """
        try:
            ser.write(constant)
            start_timer = time.time() # start a timer
            while True:
                output = ser.readline().decode("utf-8")
                if len(output) > 4:
                    break
                delta = time.time() - start_timer
                if delta >= 3: # wait 3 seconds to see if data arrives
                    output = '0' # no data recieved
                    break
            output = output.split(",")[2].strip()[0:8]
        except:
            output = '0'
        return output

    # Redefine abstract method to poll a machine for data
    def _poll_machine(self):
        """Polls Haas hardware interface and returns data reccieved

        Returns
        -------
        Dict[Any, str]
            machine data received from the Haas hardware interface
        """
        # Read in Haas constants from yaml file
        with open('haas_constants.yaml', 'r') as haas_constants:
            constants_dict = yaml.load(haas_constants, Loader=lf_utils.yaml_loader.Loader)

        # Begin fetching data from Haas
        try:
            # Coolant Level Data
            coolant_lvl = get_data(self._serial_port, constants_dict['COOLANT_LEVEL'])
            machine_data['Coolant Level'] = coolant_lvl

            # Spindle Speed RPM
            spindle_spd = get_data(self._serial_port, constants_dict['SPINDLE_SPEED'])
            machine_data['Spindle Speed'] = spindle_spd

            # Machine Coords (X, Y, Z, A, B)
            machine_x = get_data(self._serial_port, constants_dict['MACHINE_COORD_X'])
            machine_data['Machine Coordinate X Value'] = machine_x

            machine_y = get_data(self._serial_port, constants_dict['MACHINE_COORD_Y'])
            machine_data['Machine Coordinate Y Value'] = machine_y

            machine_z = get_data(self._serial_port, constants_dict['MACHINE_COORD_Z'])
            machine_data['Machine Coordinate Z Value'] = machine_z

            machine_a = get_data(self._serial_port, constants_dict['MACHINE_COORD_A'])
            machine_data['Machine Coordinate A Value'] = machine_a

            machine_b = get_data(self._serial_port, constants_dict['MACHINE_COORD_B'])
            machine_data['Machine Coordinate B Value'] = machine_b

            # Work Coords (X, Y, Z, A, B)
            work_x = get_data(self._serial_port, constants_dict['WORK_COORD_X'])
            machine_data['Work Coordinate X Value'] = work_x

            work_y = get_data(self._serial_port, constants_dict['WORK_COORD_Y'])
            machine_data['Work Coordinate Y Value'] = work_y

            work_z = get_data(self._serial_port, constants_dict['WORK_COORD_Z'])
            machine_data['Work Coordinate Z Value'] = work_z

            work_a = get_data(self._serial_port, constants_dict['WORK_COORD_A'])
            machine_data['Work Coordinate A Value'] = work_a

            work_b = get_data(self._serial_port, constants_dict['WORK_COORD_B'])
            machine_data['Work Coordinate B Value'] = work_b

        except Exception as ex:
            print("Failed to retrive any data from machine" + str(ex))
            time.sleep(2)
    
        self._serial_port.close()

        # Return the dictionary of data
        return machine_data
