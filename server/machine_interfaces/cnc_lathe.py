from typing import Any, Dict, Tuple
import struct

from .base import MachineInterface
from server.hardware.bt import BluetoothPort 


class CNCLatheInterface(MachineInterface):
    """Provides an `interface for the CNC Lathe (Ecoca)"""
    def __init__(self, publish_port: int, machine_config: Dict):
        """Initialize bluetooth connection with CNC lathe.

        Parameters
        ----------
        publish_port : int
            port to publish data to
        machine_config : Dict
            machine hardware interface configuration dictionary
        """
        # init base class
        super().__init__(publish_port, machine_config)

        # set up bluetooth port and bind to Ecoca interface
        self._bt_port = BluetoothPort(**self.machine_config["bt_params"])
    
    def _poll_machine(self) -> Dict[Any, str]:
        """Polls CNC Lathe for data

        Returns
        -------
        Dict[Any, str]
            machine data gotten from CNC lathe hardware interface
        """
        # read message from bluetooth port
        msg = BluetoothPort.get_msg(8)

        # parse message
        door_open, spindle_speed = self._parse_msg(msg)

        return {
            "status": {"door_open": door_open},
            "rates": {"spindle_speed": spindle_speed},
        }

    def _parse_msg(self, msg: bytes) -> Tuple[bool, int]:
        """Parses message into door open and spindle speed fields.

        Parameters
        ----------
        msg : bytes
            raw message in btyes

        Returns
        -------
        Tuple[bool, int]
            fields parsed from message
        """
        # assert that delimiters are correct
        if not msg[1] == b',' and msg[4] == b',' and msg[7] == b';':
            raise RuntimeError("Message is malformed. Incorrect delimiters.")

        # get door open and spindle speed
        door_open = struct.unpack('?', msg[0])
        spindle_speed = struct.unpack('H', msg[2:4])

        # get and check checksum
        checksum = struct.unpack('H', msg[5:7])
        derived_checksum = int(door_open) + spindle_speed
        if checksum != derived_checksum:
            raise RuntimeError(
                f"Derived checksum {derived_checksum} does not match message checksum {checksum}."
            )

        return door_open, spindle_speed
