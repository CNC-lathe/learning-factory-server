from typing import Any, Dict, Tuple
import copy
import random
import pickle
import string
import time
import threading
import unittest
import zmq

from server.machine_interfaces import HaasInterface
from lf_utils import retry

class MockHaasInterface(HaasInterface):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        super().__init__(*args, **kwargs)

        self._return_machine_data = False
        self._wait_interval = 0.01

    def set_machine_data(self, machine_data: Dict[str, Any]):
        self._mock_machine_data = machine_data
        self._return_machine_data = True
    

class HaasInterfaceTests(unittest.TestCase):
    # Test port
    test_port = 49152

    def setUp(self):
        # create receive socket
        self._context = zmq.Context()
        receive_address = f"tcp://*:{self.test_port}"
        self.receive_socket = self._context.socket(zmq.SUB)
        retry(
            self.receive_socket.bind,
            receive_address,
            handled_exceptions=zmq.error.ZMQError,
        )

        # subscribe to mock Haas interface topic
        self.receive_socket.setsockopt(zmq.SUBSCRIBE, b"mock_haas")

        # initialize mock Haas interface (create a virtual serial port with 'socat -d -d pty,raw,echo=0 pty,raw,echo=0')
        self.machine_interface = MockHaasInterface(self.test_port, {"Haas CNC": "mock_haas"}, "/dev/pts/0")

        # start mock Haas interface
        self.machine_interface.run()
        print("Finishing setUp")

    def tearDown(self):
        self.machine_interface.stop()

        time.sleep(0.5)
        self._context.destroy()

    def recv(self) -> Tuple[bytes, Dict[str, Any]]:
        machine_name, machine_data_encoded = self.receive_socket.recv_multipart()

        return machine_name, pickle.loads(machine_data_encoded)

    def test_machine(self):
        
        # check that machine data is received correctly
        returned_machine_name, returned_machine_data = self.recv()
        self.assertEqual(b"mock_haas", returned_machine_name)
        self.assertDictEqual(machine_data, returned_machine_data)
