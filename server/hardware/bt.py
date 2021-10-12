"""Bluetooth port wrapper."""
from typing import Optional

import bluetooth


class BluetoothPort:
    def __init__(self, uuid: str):
        """Initializes bluetooth port and binds to UUID.

        Parameters
        ----------
        uuid : str
            service UUID to bind to
        """
        raise NotImplementedError

    def get_msg(self, msg_len: int) -> bytes:
        """Gets message from Bluetooth port of provided length.

        Parameters
        ----------
        msg_len : int
            number of bytes to read from bluetooth port
        """
        self._port.recv(msg_len)
