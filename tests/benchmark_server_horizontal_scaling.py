from typing import Any, Dict, Tuple
import copy
import multiprocessing as mp
import random
import pickle
import time
import unittest

import tqdm
import zmq

from server import LFServer
from lf_utils import retry


NUM_INTERFACES = 20
NUM_FIELDS = 100
NUM_SERVERS = 4


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
        f"machine_{ii}": {
            "_target_": "tests.test_server.MockMachineInterface",
            "machine_name": "machine_{ii}"
        }
        for ii in range(NUM_INTERFACES)
    }

    def setUp(self):
        """Initializes and starts LFServer, creates ZMQ sockets for outputs
        """
        # initialize LFServers
        self.servers = []
        for ii in range(NUM_SERVERS):
            self.servers.append(LFServer(
                self.data_port + ii,
                {
                    k: v
                    for jj, (k, v) in enumerate(self.machine_configs.items())
                    if jj % NUM_SERVERS == ii
                }
            ))

        # start LFServers
        for server in self.servers:
            server.start()

        # create output ZMQ sockets
        self.context = zmq.Context()

        self.data_sockets = [self.context.socket(zmq.SUB) for ii in range(NUM_SERVERS)]
        for sock in self.data_sockets:
            retry(
                sock.connect,
                f"tcp://127.0.0.1:{self.data_port + ii}",
                handled_exceptions=zmq.error.ZMQError
            )

    def tearDown(self):
        """Stops LFServer, destroys ZMQ sockets"""
        # stop LFServer (first need to bypass blocking recv call)
        for server in self.servers:
            tuple(server.machine_interfaces.values())[0].send_data(None)
            server.stop()

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
        for ii, data_socket in enumerate(self.data_sockets):
            for jj, topic in enumerate(topics):
                if jj % NUM_SERVERS  == ii:
                    data_socket.setsockopt(zmq.SUBSCRIBE, topic)

        time.sleep(1)

    def _get_machine_interface(self, interface_idx: int) -> MockMachineInterface:
        """Gets machine interface corresponding to interface index."""
        for ii, server in enumerate(self.servers):
            if interface_idx % (ii + 1) == 0:
                return server.machine_interfaces[f"machine_{ii}"]

    def test_lf_server_run_multiple_machines(self):
        """Tests run method of LFServer with multiple machines producing data"""
        # create machine data dicts
        machine_data_dicts = [
            [
                {f"field{ii}": random.random() for ii in range(NUM_FIELDS)}
                for _ in range(NUM_INTERFACES)
            ]
            for _ in range(100)
        ]

        # subscribe to machine topics
        self._subscribe_to_topics(*(f"machine_{ii}".encode() for ii in range(NUM_INTERFACES)))

        # iterate over machine data dicts
        for machine_data_dict_at_ts in tqdm.tqdm(machine_data_dicts):
            # send machine data dict through mock machine interface
            with mp.Pool(NUM_INTERFACES) as p:
                for ii, machine_data_dict in enumerate(machine_data_dict_at_ts):
                    p.map_async(self._get_machine_interface(ii).send_data, machine_data_dict)

            # get dicts sent to digital dashboard socket
            data_dicts = (
                self._recv(data_socket)
                for _ in range(NUM_INTERFACES // NUM_SERVERS)
                for data_socket in self.data_sockets
            )


