from typing import Any, Dict, Tuple
from threading import Thread
import pickle
import socket

import zmq

from .utils import instantiate, retry
from .machine_interfaces import MachineInterface


class LFServer(Thread):
    """Learning Factory Server

    Handles receiving data from machine interfaces and
    sending data to digital dashboard and virtual factory
    """
    machine_interfaces: Dict[str, MachineInterface]

    def __init__(
            self,
            digital_dash_ip_addr: str,
            digital_dash_port: int,
            virtual_factory_ip_addr: str,
            virtual_factory_port: int,
            machine_configs: Dict[str, Dict]
    ):
        """Initializes server thread, instantiates and starts machine interfaces,
        and sets up ZMQ sockets to machines and digital dashboard and virtual factory

        Parameters
        ----------
        digital_dash_ip_addr : str
            IP address of digital dashboard
        digital_dash_port : int
            port of digital dashboard
        virtual_factory_ip_addr : str
            IP address of virtual factory
        virtual_factory_port : int
            port of virtual factory
        machine_configs : Dict[str, Dict]
            machine interface configs, used to instantiate machine interfaces
        """
        # create digital dashboard, virtual factory sockets
        self._context = zmq.Context()

        digital_dash_address = f"tcp://{digital_dash_ip_addr}:{digital_dash_port}"
        self._digital_dash_socket = self._context.socket(zmq.PUSH)
        retry(
            self._digital_dash_socket.connect,
            digital_dash_address,
            handled_exceptions=zmq.error.ZMQError
        )

        virtual_factory_address = f"tcp://{virtual_factory_ip_addr}:{virtual_factory_port}"
        self._virtual_factory_socket = self._context.socket(zmq.PUSH)
        retry(
            self._virtual_factory_socket.connect,
            virtual_factory_address,
            handled_exceptions=zmq.error.ZMQError
        )

        # create receive socket and bind to receive address
        receive_port = self._get_free_port()
        self._receive_address = f"tcp://*:{receive_port}"
        self._receive_socket = self._context.socket(zmq.SUB)
        retry(
            self._receive_socket.bind,
            self._receive_address,
            handled_exceptions=zmq.error.ZMQError
        )

        # subscribe to all topics on receive socket
        self._receive_socket.setsockopt(zmq.SUBSCRIBE, b"")

        # set port in machine configs
        for machine_conf in machine_configs.values():
            machine_conf["port"] = receive_port

        # instantiate machine interfaces
        self.machine_interfaces = {
            machine_name: instantiate(machine_config)
            for machine_name, machine_config in machine_configs.items()
        }

        # start machine interfaces
        for machine_interface in self.machine_interfaces.values():
            machine_interface.start()

        # initialize thread
        Thread.__init__(self)
        self.stopped = False

    def run(self):
        """Runs main thread, receiving machine data from machine interfaces and
        sending that data to digital dashboard, virtual factory
        """
        try:
            # loop until thread is stopped
            while not self.stopped:
                # receive data from machine interfaces (blocking)
                machine_name, machine_data = self._recv_data()

                # send data to digital dashboard, virtual factory
                self._send_data({machine_name: machine_data})

        # catch keyboard interrupts and gracefully exit thread
        except KeyboardInterrupt:
            pass

        self._exit_thread()

    def stop(self):
        """Asynchronously stops server thread"""
        self.stopped = True

    def _recv_data(self) -> Tuple[str, Dict[str, Dict[str, Any]]]:
        """Receives and returns data from receive socket

        Returns
        -------
        Tuple[str, Dict[str, Dict[str, Any]]]
            tuple of machine name and machine data dictionary
        """
        machine_name, machine_data_encoded = self._receive_socket.recv_multipart()

        return machine_name, pickle.loads(machine_data_encoded)

    def _send_data(self, machine_data: Dict[str, Dict[str, Any]]):
        """Sends machine data to digital dashboard, virtual factory

        Parameters
        ----------
        machine_data : Dict[str, Dict[str, Any]]
            machine data dictionary to send
        """
        # send machine data to digital dashboard
        self._digital_dash_socket.send_pyobj(machine_data)

        # send machine data to virtual factory
        self._virtual_factory_socket.send_pyobj(machine_data)

    def _exit_thread(self):
        """Stops machine interfaces and closes zmq sockets"""
        # stop machine interfaces
        for machine_interface in self.machine_interfaces.values():
            machine_interface.stop()

        # destroy zmq context
        self._context.destroy()

    @staticmethod
    def _get_free_port() -> int:
        """Gets random free port from OS

        Returns
        -------
        int
            port number, generated by OS
        """
        # generate free port
        free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        free_socket.bind(("", 0))
        receive_port = free_socket.getsockname()[-1]

        # close socket
        free_socket.close()

        # return port number
        return receive_port
