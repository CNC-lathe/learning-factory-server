from typing import Any, Dict, Tuple
import copy
import random
import pickle
import string
import time
import threading
import unittest

import zmq

from server.machine_interfaces import MachineInterface
from lf_utils import retry


class MockMachineInterface(MachineInterface):
    """Mocks machine interface (with blocking poll machine function)"""
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        super().__init__(*args, **kwargs)

        self._return_machine_data = False
        self._wait_interval = 0.01

    def set_machine_data(self, machine_data: Dict[str, Any]):
        """Method used to set machine data to return from interface."""
        self._mock_machine_data = machine_data
        self._return_machine_data = True
        
    def _poll_machine(self) -> Dict[str, Any]:
        while not self._return_machine_data:
            time.sleep(self._wait_interval)

        self._return_machine_data = False

        return self._mock_machine_data


class MachineInterfaceTests(unittest.TestCase):
    """Tests MachineInterface base class implementation"""
    # data output port
    data_port = 49152

    def setUp(self):
        """Creates receive socket, initializes and starts mock machine interface."""
        # create receive socket
        self._context = zmq.Context()
        receive_address = f"tcp://*:{self.data_port}"
        self.receive_socket = self._context.socket(zmq.SUB)
        retry(
            self.receive_socket.bind,
            receive_address,
            handled_exceptions=zmq.error.ZMQError,
        )

        # subscribe to mock machine interface topic
        self.receive_socket.setsockopt(zmq.SUBSCRIBE, b"mock_machine")

        # initialize mock machine interface
        self.machine_interface = MockMachineInterface(self.data_port, {"name": "mock_machine"})

        # start mock machine interface
        self.machine_interface.start()

    def tearDown(self):
        """Closes zmq context and stops machine interface."""
        self.machine_interface.set_machine_data(None)
        self.machine_interface.stop()

        time.sleep(0.5)
        self._context.destroy()

    def recv(self) -> Tuple[bytes, Dict[str, Any]]:
        """Receives machine data on receive socket and returns machine name and data."""
        machine_name, machine_data_encoded = self.receive_socket.recv_multipart()

        return machine_name, pickle.loads(machine_data_encoded)

    def test_send_one_message_and_check_received_correctly(self):
        """Sends one message via mock machine interface and checks that it's received correctly."""
        # create mock machine data and set it to be sent by machine interface
        machine_data = {"x": 5, "y": 6, "z": 7, "abc": "asdf"}
        self.machine_interface.set_machine_data(machine_data)

        # check that machine data is received correctly
        returned_machine_name, returned_machine_data = self.recv()
        self.assertEqual(b"mock_machine", returned_machine_name)
        self.assertDictEqual(machine_data, returned_machine_data)

    def test_send_many_messages_and_check_received_correctly(self):
        """Sends many messages via mock interface and checks that they're received correctly."""
        def gen_mock_machine_data() -> Dict[str, Any]:
            return {
                "x": random.randint(0, 100),
                "y": random.randint(0, 100),
                "z": random.randint(0, 100),
                "abc": "".join(random.choices(string.ascii_letters, k=5))
            }

        for _ in range(100):
            # set machine data using generator
            machine_data = gen_mock_machine_data()
            self.machine_interface.set_machine_data(machine_data)

            # check that machine data is received correctly
            returned_machine_name, returned_machine_data = self.recv()
            self.assertEqual(b"mock_machine", returned_machine_name)
            self.assertDictEqual(machine_data, returned_machine_data)

