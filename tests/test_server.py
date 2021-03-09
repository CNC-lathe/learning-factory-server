from typing import Any, Dict, Tuple
import copy
import random
import pickle
import unittest

import zmq

from server import LFServer
from lf_utils import retry


class MockMachineInterface:
    """Mocks machine interface"""
    def __init__(self, port: int, machine_name: str):
        """Initializes mock machine interface,  ZMQ socket

        Parameters
        ----------
        port : int
            port to send mock machine data over
        machine_name : str
            name of machine (to use as ZMQ topic)
        """
        # initialize socket
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        retry(
            self.socket.connect,
            f"tcp://127.0.0.1:{self.port}",
            handled_exceptions=zmq.error.ZMQError
        )

        # set machine name
        self.machine_name = machine_name

    def start(self):
        """Mock start method"""
        pass

    def stop(self):
        """Mock stop method"""
        pass

    def send_data(self, data_dict: Dict[str, Any]):
        """Sends data dict over ZMQ socket"""
        self.socket.send_multipart([bytes(self.machine_name, "utf-8"), pickle.dumps(data_dict)])


class LFServerTests(unittest.TestCase):
    """Tests Learning Factory Server"""
    # output IP addresses, ports
    digital_dash_ip_port: Tuple[str, int] = ("127.0.0.1", 49152)
    virtual_factory_ip_port: Tuple[str, int] = ("127.0.0.1", 49153)

    # machine configs (for MockMachineInterface objects)
    machine_configs = {
        "machine_1": {
            "_target_": "tests.test_server.MockMachineInterface",
            "machine_name": "machine_1"
        },
        "machine_2": {
            "_target_": "tests.test_server.MockMachineInterface",
            "machine_name": "machine_2"
        }
    }

    def setUp(self):
        """Initializes and starts LFServer, creates ZMQ sockets for outputs
        """
        # initialize LFServer
        self.server = LFServer(
            *self.digital_dash_ip_port,
            *self.virtual_factory_ip_port,
            copy.deepcopy(self.machine_configs)
        )

        # start LFServer
        self.server.start()

        # create output ZMQ sockets
        self.context = zmq.Context()

        self.digital_dash_socket = self.context.socket(zmq.PULL)
        retry(
            self.digital_dash_socket.bind,
            f"tcp://*:{self.digital_dash_ip_port[-1]}",
            handled_exceptions=zmq.error.ZMQError
        )

        self.virtual_factory_socket = self.context.socket(zmq.PULL)
        retry(
            self.virtual_factory_socket.bind,
            f"tcp://*:{self.virtual_factory_ip_port[-1]}",
            handled_exceptions=zmq.error.ZMQError
        )

    def tearDown(self):
        """Stops LFServer, destroys ZMQ sockets"""
        # stop LFServer (first need to bypass blocking recv call)
        self.server.machine_interfaces["machine_1"].send_data(None)
        self.server.stop()

        # flush digital dash, virtual factory sockets
        self._recv(self.digital_dash_socket)
        self._recv(self.virtual_factory_socket)

        # destroy context
        self.context.destroy()

    def _recv(self, socket: zmq.Socket) -> Dict[str, Dict[str, Any]]:
        """Receives and returns message on socket

        Parameters
        ----------
        socket : zmq.Socket
            socket to receive message from

        Returns
        -------
        Dict[str, Dict[str, Any]]
            nested data dictionary received on socket
        """
        return socket.recv_pyobj()

    def test_lf_server_run_single_machine(self):
        """Tests run method of LFServer with a single machine producing data"""
        # create machine data dicts
        machine_data_dicts = [
            {"field1": random.random(), "field2": random.random(), "field3": random.random()}
            for _ in range(100)
        ]

        # iterate over machine data dicts
        for machine_data_dict in machine_data_dicts:
            # send machine data dict through mock machine interface
            self.server.machine_interfaces["machine_1"].send_data(machine_data_dict)

            # build truth data dict
            truth_data_dict = {b"machine_1": machine_data_dict}

            # check that machine data dict is received by digital dash, virtual factory sockets
            self.assertDictEqual(truth_data_dict, self._recv(self.digital_dash_socket))
            self.assertDictEqual(truth_data_dict, self._recv(self.virtual_factory_socket))


    def test_lf_server_run_multiple_machines(self):
        """Tests run method of LFServer with multiple machines producing data"""
        # create machine data dicts
        machine_data_dicts = [
            (
                {"field1": random.random(), "field2": random.random(), "field3": random.random()},
                {"other_field1": random.random(), "other_field2": "CONSTANT"}
            )
            for _ in range(100)
        ]

        # iterate over machine data dicts
        for machine1_data_dict, machine2_data_dict in machine_data_dicts:
            # send machine data dict through mock machine interface
            self.server.machine_interfaces["machine_1"].send_data(machine1_data_dict)
            self.server.machine_interfaces["machine_2"].send_data(machine2_data_dict)

            # build truth data dicts
            truth_data_dicts = [{b"machine_1": machine1_data_dict}, {b"machine_2": machine2_data_dict}]

            # get dicts sent to digital dashboard socket
            digital_dash_dicts = (
                self._recv(self.digital_dash_socket), self._recv(self.digital_dash_socket)
            )

            # get dicts sent to virtual factorysocket
            virtual_factory_dicts = (
                self._recv(self.virtual_factory_socket), self._recv(self.virtual_factory_socket)
            )

            # check that correct dicts were received by each socket, order-irrespective
            self.assertCountEqual(truth_data_dicts, digital_dash_dicts)
            self.assertCountEqual(truth_data_dicts, virtual_factory_dicts)
