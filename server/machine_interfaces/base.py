from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
from threading import Thread
import socket

import zmq


class MachineInterface(Thread, ABC):
    """Defines Machine Interface base class"""
    def __init__(self, publish_port: Optional[int], machine_config: Dict):
        """Initializes machine hardware interface, thread, and publisher socket

        Parameters
        ----------
        publish_port : Optional[int]
            port to publish data to
        machine_config : Dict
            machine hardware interface configuration dictionary
        """
        # set machine config
        self._machine_config = machine_config

        # set machine name
        self._machine_name = self._machine_config["name"]

        # set up publish address
        if publish_port is None:
            publish_port = self._get_free_port()

        self._publish_address = f"tcp://*:{publish_port}"

        # set up publish socket
        self._context = zmq.Context()
        self._publish_socket = self._context.socket(zmq.PUB)
        self._publish_socket.bind(self._publish_address)

        # initialize thread
        Thread.__init__(self)
        self._stopped = False

    def run(self):
        """Polls machine hardware and publishes received machine data
        """
        # loop until thread is stopped
        while not self._stopped:
            # get machine data
            machine_data = self._poll_machine()

            # publish machine data
            self._publish_data(self._publish_socket, self._machine_name, machine_data)

        # close ZMQ socket and context
        self._close_zmq()

    def stop(self):
        """Stops thread asynchronously"""
        self._stopped = True

    @abstractmethod
    @staticmethod
    def _poll_machine() -> Dict[Any, str]:
        """Polls machine hardware interface and returns machine data received

        Returns
        -------
        Dict[Any, str]
            machine data recieved of machine hardware interface
        """
        ...

    @staticmethod
    def _publish_data(publish_socket: zmq.Socket, machine_name: str, machine_data: Dict[Any, str]):
        """Publishes machine data over publish socket

        Parameters
        ----------
        publish_socket : zmq.Socket
            socket to publish
        machine_name : str
            name of machine interface, used as topic for publishing
        machine_data : Dict[Any, str]
            machine data dictionary to publish
        """
        publish_socket.send_multipart([bytes(machine_name, "utf-8"), machine_data])

    def _close_zmq(self):
        """Closes ZMQ context and socket
        """
        # unbind socket and destroy context
        self._publish_socket.unbind(self._publish_address)
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
        publish_port = free_socket.getsockname()[-1]

        # close socket
        free_socket.close()

        # return port number
        return publish_port
