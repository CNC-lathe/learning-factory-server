# Luke Minton, MDE Fall 2021, VT ISE Learning Factory, Interface from Haas CNC machine to LF server
# Machine currently has a serial (RS232) to USB port going into a Raspberry Pi (Canakit): Assuming this was used for previous data collection
# DONE: Test in LF by directly plugging into Haas and then debug
# RESULT: Retrieved data from the Haas over serial to USB cable, I do not have the qualifications to run an actual job on the Haas but data
# reception was verified by seeing a value returned for the coolant level and monitoring the sending of macros and recieving of data through
# free software called Serial Port Monitor

import socket, serial, time, sys
from base import MachineInterface

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

# Network macros
HOST = 'localhost'
PORT = 7878

# Inherit from the Machine Interface class defined in base.py
class HaasInterface(MachineInterface):
            
    # Redefine abstract method to poll a machine for data
    def _poll_machine():

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

        # Helper function to create a socket
        def socket_init():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error as err:
                print("Failed to create socket, Error: " + str(err[0] + " Message " + msg[1]))
                sys.exit()
            
            try:
                s.bind((HOST, PORT))
            except socket.error as err:
                print("Failed to bind, Error: " + str(err[0] + " Message " + msg[1]))
                sys.exit()
            
            s.listen(5)

        # Open a socket for Haas socket communication
        socket_init()

        # Define serial port for Haas data communication (/dev/pts/0 represents a virtual serial port used for testing)
        # Direct USB to serial connection would use a COM port such as COM11
        serial_port = serial.Serial(port = "/dev/pts/0", baudrate = 9600, bytesize = serial.SEVENBITS, xonxoff = True, timeout = 5)

        # Attempt to open a serial port for communication with the Haas
        try:
            serial_port.open()
        except serial.SerialException:
            if serial_port.is_open:
                try:
                    print("Port was open, attempting to close and reopen")
                    serial_port.close()
                    time.sleep(2)
                    serial_port.open()
                except:
                    print("Failed to close port")
                    event.clear()
            else:
                print("Failed to connect to serial port, either in use or does not exist")
                event.clear() 
        
        # Error checking statement
        print("CHECK")

        # Define a dictionary for data housing
        data_dict = {}

        # Begin fetching data from Haas
        while True:
            try:
                # Coolant Level Data
                coolant_lvl = ''
                coolant_lvl = get_data(serial_port, COOLANT_LEVEL, coolant_lvl)
                data_dict['Coolant Level'] = coolant_lvl
                print("Coolant level: " + coolant_lvl)

                # Spindle Speed RPM
                spindle_spd = ''
                spindle_spd = get_data(serial_port, SPINDLE_SPEED, spindle_spd)
                data_dict['Spindle Speed'] = spindle_spd
                print("Spindle speed: " + spindle_spd)

                # Machine Coords (X, Y, Z, A, B)
                machine_x = ''
                machine_x = get_data(serial_port, MACHINE_COORD_X, machine_x)
                data_dict['Machine Coordinate X Value'] = machine_x
                print("Machine coordinate X: " + machine_x)

                machine_y = ''
                machine_y = get_data(serial_port, MACHINE_COORD_Y, machine_y)
                data_dict['Machine Coordinate Y Value'] = machine_y
                print("Machine coordinate Y: " + machine_y)

                machine_z = ''
                machine_z = get_data(serial_port, MACHINE_COORD_Z, machine_z)
                data_dict['Machine Coordinate Z Value'] = machine_z
                print("Machine coordinate Z: " + machine_z)

                machine_a = ''
                machine_a = get_data(serial_port, MACHINE_COORD_A, machine_a)
                data_dict['Machine Coordinate A Value'] = machine_a
                print("Machine coordinate A: " + machine_a)

                machine_b = ''
                machine_b = get_data(serial_port, MACHINE_COORD_B, machine_b)
                data_dict['Machine Coordinate B Value'] = machine_b
                print("Machine coodinate B: " + machine_b)

                # Work Coords (X, Y, Z, A, B)
                work_x = ''
                work_x = get_data(serial_port, WORK_COORD_X, work_x)
                data_dict['Work Coordinate X Value'] = work_x
                print("Work coordinate X: " + work_x)

                work_y = ''
                work_y = get_data(serial_port, WORK_COORD_Y, work_y)
                data_dict['Work Coordinate Y Value'] = work_y
                print("Work coordinate Y: " + work_y)

                work_z = ''
                work_z = get_data(serial_port, WORK_COORD_Z, work_z)
                data_dict['Work Coordinate Z Value'] = work_z
                print("Work coordinate Z: " + work_z)

                work_a = ''
                work_a = get_data(serial_port, WORK_COORD_A, work_a)
                data_dict['Work Coordinate A Value'] = work_a
                print("Work coordinate A: " + work_a)

                work_b = ''
                work_b = get_data(serial_port, WORK_COORD_B, work_b)
                data_dict['Work Coordinate B Value'] = work_b
                print("Work coordinate B: " + work_b)

            except Exception as ex:
                print("Failed to retrive any data from machine" + str(ex))
                time.sleep(2)
    
        serial_port.close()

        # Return the dictionary of data
        return data_dict

# Used to directly call the poll machine method for testing
HaasInterface._poll_machine()
        