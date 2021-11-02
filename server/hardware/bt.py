"""Bluetooth port wrapper."""
from typing import Optional

import bluetooth


class BluetoothPort:
    def __init__(self, uuid: str, port: int):
        """Initializes bluetooth port and connects to bluetooth service.

        Parameters
        ----------
        uuid : str
            service UUID to connect to
        port : int
            port to connect to
        """
        self._port = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self._port.connect((uuid, port))

    def get_msg(self, msg_len: int) -> bytes:
        """Gets message from Bluetooth port of provided length.

        Parameters
        ----------
        msg_len : int
            number of bytes to read from bluetooth port

        Returns
        -------
        bytes
            message received from bluetooth port
        """
        return self._port.recv(msg_len)
