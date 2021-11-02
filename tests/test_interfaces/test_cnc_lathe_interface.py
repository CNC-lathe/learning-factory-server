from typing import Optional, Tuple

import struct
import unittest
from unittest import mock

from server import hardware
from server import machine_interfaces
from server.machine_interfaces import MachineInterface
from server.machine_interfaces.cnc_lathe import CNCLatheInterface


class CNCLatheInterfaceTests(unittest.TestCase):
    """Tests the CNC lathe interface."""
    msg_format: str = "!?sHsHs"

    def _build_message(
        self,
        door_open: bool,
        spindle_speed: int,
        delims: Optional[Tuple[str]] = None,
        checksum: Optional[int] = None,
    ) -> bytes:
        """Builds a byte string message from parameters provided.

        Parameters
        ----------
        door_open : bool
            if the door is open or closed
        spindle_speed : int
            the integer value of spindle speed
        delims : Optional[Tuple[str]], optional
            tuple of delimiters to use, by default None
            will default to commas for field delimiters and semi-colons for message delimiter
        checksum : Optional[int], optional
            checksum value to use, by default None
            will defalut to calculating it frmo the door open and spindle speed values

        Returns
        -------
        bytes
            byte string representation of message
        """
        # get default delims if necessary
        if delims is None:
            delims = (",", ",", ";")

        # get default checksum if necessary
        if checksum is None:
            checksum = int(door_open) + spindle_speed

        # build and return message
        field_delim_1, field_delim_2, msg_delim = delims
        return struct.pack(
            self.msg_format,
            door_open,
            field_delim_1.encode(),
            spindle_speed,
            field_delim_2.encode(),
            checksum,
            msg_delim.encode(),
        )

    def build_machine_interface(self) -> CNCLatheInterface:
        """Builds and returns machine interface

        Returns
        -------
        CNCLatheInterface
            constructed machine interface
        """
        patcher = mock.patch.object(MachineInterface, "__init__", mock.Mock)
        with patcher:
            patcher.is_local = True
            interface = CNCLatheInterface(None, {"bt_params": {"uuid": None, "port": None}})

        return interface


    @mock.patch("server.hardware.BluetoothPort")
    def test_cnc_lathe_errors_with_improperly_delimited_message(self, mock_bt: mock.patch):
        """Tests that CNC lathe `poll_machine` method errors when message is improperly delimited."""
        # instantiate lathe interface
        machine_interface = self.build_machine_interface()

        # check that error is raised with incorrect first field delimiter
        machine_interface._bt_port.get_msg.return_value = self._build_message(
            False, 0, delims=("X", ",", ";")
        )
        with self.assertRaises(RuntimeError):
            machine_interface._poll_machine()

        # check that error is raised with incorrect second field delimiter
        machine_interface._bt_port.get_msg.return_value = self._build_message(
            False, 0, delims=(",", "X", ";")
        )
        with self.assertRaises(RuntimeError):
            machine_interface._poll_machine()

        # check that error is raised with incorrect message field delimiter
        machine_interface._bt_port.get_msg.return_value = self._build_message(
            False, 0, delims=(",", ",", "X")
        )
        with self.assertRaises(RuntimeError):
            machine_interface._poll_machine()

    @mock.patch("server.hardware.BluetoothPort")
    def test_cnc_lathe_parses_message_correctly(self, mock_bt: mock.patch):
        """Tests that CNC lathe `poll_machine` method parses messages correctly."""
        # instantiate lathe interface
        machine_interface = self.build_machine_interface()
    
        # check that message is parsed with door open and spindle speed of 1234
        machine_interface._bt_port.get_msg.return_value = self._build_message(True, 1234)
        parsed_message = machine_interface._poll_machine()
        self.assertCountEqual(
            {"status": {"door_open": True}, "rates": {"spindle_speed": 1234}},
            parsed_message,
        )
    
        # check that message is parsed with door closed and spindle speed of 5
        machine_interface._bt_port.get_msg.return_value = self._build_message(False, 5)
        parsed_message = machine_interface._poll_machine()
        self.assertCountEqual(
            {"status": {"door_open": False}, "rates": {"spindle_speed": 5}},
            parsed_message,
        )
