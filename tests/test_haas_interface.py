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

        self._return_haas_data = False
        self._wait_interval = 0.01

    def set_haas_data(self, haas_data: Dict[str, Any]):
        self._mock_haas_data = haas_data
        self._return_haas_data = True
    

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
        # this is the key to this interface testing, a mock version of a serial port to "send" data through
        self.haas_interface = MockHaasInterface(self.test_port, {"Haas CNC": "mock_haas"}, "/dev/pts/0")

        # start mock Haas interface
        self.haas_interface.run()
        print("Finishing setUp")

    def tearDown(self):
        self.haas_interface.stop()

        time.sleep(0.5)
        self._context.destroy()

    def recv(self) -> Tuple[bytes, Dict[str, Any]]:
        machine_name, haas_data_encoded = self.receive_socket.recv_multipart()

        return machine_name, pickle.loads(haas_data_encoded)

    def test_haas_one_time(self):
        
        # check that machine data is received correctly
        returned_machine_name, returned_haas_data = self.recv()
        self.assertEqual(b"mock_haas", returned_machine_name)
        self.assertDictEqual(haas_data, returned_haas_data)

    def test_haas_continuous(self):

        def create_mock_haas_data() -> Dict[str, Any]:
            return {
            "Coolant Level": random.randint(20000, 50000),
            "Spindle Speed": random.randint(100, 300),
            "Machine Coordinate X Value": random.randint(0, 99),
            "Machine Coordinate Y Value": random.randint(0, 99),
            "Machine Coordinate Z Value": random.randint(0, 99),
            "Machine Coordinate A Value": random.randint(0, 99),
            "Machine Coordinate B Value": random.randint(0, 99),
            "Work Coordinate X Value": random.randint(0, 99),
            "Work Coordinate Y Value": random.randint(0, 99),
            "Work Coordinate Z Value": random.randint(0, 99),
            "Work Coordinate A Value": random.randint(0, 99),
            "Work Coordinate B Value": random.randint(0, 99)
            }

        for _ in range(100):
            haas_data = create_mock_haas_data()
            self.haas_interface.set_haas_data(haas_data)

            returned_machine_name, returned_haas_data = self.recv()
            self.assertEqual(b"mock_haas", returned_machine_name)
            self.assertDictEqual(haas_data, returned_haas_data)