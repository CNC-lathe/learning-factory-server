from typing import Any, Dict, Tuple
import struct

from .base import MachineInterface
from server import hardware


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
        self._bt_port = hardware.BluetoothPort(**machine_config["bt_params"])

        # set failure mode
        self._fail_hard = machine_config.get("fail_hard", False)
    
    def _poll_machine(self) -> Dict[Any, str]:
        """Polls CNC Lathe for data

        Returns
        -------
        Dict[Any, str]
            machine data gotten from CNC lathe hardware interface
        """
        # read message from bluetooth port
        msg = self._bt_port.get_msg(8)

        try:
            # parse message
            door_open, spindle_speed = self._parse_msg(msg)

            return {
                "status": {"door_open": door_open},
                "rates": {"spindle_speed": spindle_speed},
            }

        except RuntimeError as err:
            if self._fail_hard:
                raise err
            else:
                raise RuntimeWarning(err.args[0])

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
        if msg[1:2] != b',' or msg[4:5] != b',' or msg[7:8] != b';':
            raise RuntimeError("Message is malformed. Incorrect delimiters.")

        # get door open and spindle speed
        door_open, *_ = struct.unpack('!?', msg[:1])
        spindle_speed, *_ = struct.unpack('!H', msg[2:4])

        # get and check checksum
        checksum, *_ = struct.unpack('!H', msg[5:7])
        derived_checksum = int(door_open) + spindle_speed
        if checksum != derived_checksum:
            raise RuntimeError(
                f"Derived checksum {derived_checksum} does not match message checksum {checksum}."
            )

        return door_open, spindle_speed
