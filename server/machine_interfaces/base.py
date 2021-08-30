from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
from threading import Thread
import pickle

import zmq

from lf_utils import retry


class MachineInterface(Thread, ABC):
    """Defines Machine Interface base class"""
    def __init__(self, publish_port: int, machine_config: Dict):
        """Initializes machine hardware interface, thread, and publisher socket

        Parameters
        ----------
        publish_port : int
            port to publish data to
        machine_config : Dict
            machine hardware interface configuration dictionary
        """
        # set machine config
        self._machine_config = machine_config

        # set machine name
        self._machine_name = self._machine_config["name"]

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
    def _poll_machine(self) -> Dict[str, Any]:
        """Polls machine hardware interface and returns machine data received

        Returns
        -------
        Dict[str, Any]
            machine data recieved of machine hardware interface
        """
        ...

    @staticmethod
    def _publish_data(publish_socket: zmq.Socket, machine_name: str, machine_data: Dict[str, Any]):
        """Publishes machine data over publish socket

        Parameters
        ----------
        publish_socket : zmq.Socket
            socket to publish
        machine_name : str
            name of machine interface, used as topic for publishing
        machine_data : Dict[str, Any]
            machine data dictionary to publish
        """
        publish_socket.send_multipart([bytes(machine_name, "utf-8"), pickle.dumps(machine_data)])

    def _close_zmq(self):
        """Closes ZMQ context and socket
        """
        # destroy context
        self._context.destroy()
