from typing import Any, Dict, Tuple
import copy
import random
import pickle
import time
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
    # data output IP address, port
    data_port = 49152

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
            self.data_port,
            copy.deepcopy(self.machine_configs)
        )

        # start LFServer
        self.server.start()

        # create output ZMQ sockets
        self.context = zmq.Context()

        self.data_socket = self.context.socket(zmq.SUB)
        retry(
            self.data_socket.connect,
            f"tcp://127.0.0.1:{self.data_port}",
            handled_exceptions=zmq.error.ZMQError
        )

    def tearDown(self):
        """Stops LFServer, destroys ZMQ sockets"""
        # stop LFServer (first need to bypass blocking recv call)
        self.server.machine_interfaces["machine_1"].send_data(None)
        self.server.stop()

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
        # poll for machine data on data socket
        if socket.poll(timeout=3000) != 0:
            machine_name, machine_data_encoded = socket.recv_multipart()
            return {machine_name: pickle.loads(machine_data_encoded)}

        else:
            self.fail("Machine data not received in time (3 seconds)")

    def _subscribe_to_topics(self, *topics: bytes):
        """Subscribes to topics on the data socket and waits 1 second."""
        for topic in topics:
            self.data_socket.setsockopt(zmq.SUBSCRIBE, topic)

        time.sleep(1)

    def test_lf_server_run_single_machine(self):
        """Tests run method of LFServer with a single machine producing data"""
        # create machine data dicts
        machine_data_dicts = [
            {"field1": random.random(), "field2": random.random(), "field3": random.random()}
            for _ in range(100)
        ]

        # subscribe to machine 1 topic
        self._subscribe_to_topics(b"machine_1")

        # iterate over machine data dicts
        for machine_data_dict in machine_data_dicts:
            # send machine data dict through mock machine interface
            self.server.machine_interfaces["machine_1"].send_data(machine_data_dict)

            # build truth data dict
            truth_data_dict = {b"machine_1": machine_data_dict}

            # check that machine data dict is received by data socket
            self.assertDictEqual(truth_data_dict, self._recv(self.data_socket))

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

        # subscribe to machine 1, 2 topics
        self._subscribe_to_topics(b"machine_1", b"machine_2")

        # iterate over machine data dicts
        for machine1_data_dict, machine2_data_dict in machine_data_dicts:
            # send machine data dict through mock machine interface
            self.server.machine_interfaces["machine_1"].send_data(machine1_data_dict)
            self.server.machine_interfaces["machine_2"].send_data(machine2_data_dict)

            # build truth data dicts
            truth_data_dicts = [{b"machine_1": machine1_data_dict}, {b"machine_2": machine2_data_dict}]

            # get dicts sent to digital dashboard socket
            data_dicts = (
                self._recv(self.data_socket), self._recv(self.data_socket)
            )

            # check that machine data dicts are received by data socket
            self.assertCountEqual(truth_data_dicts, data_dicts)

