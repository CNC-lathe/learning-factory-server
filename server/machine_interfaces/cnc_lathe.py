from typing import Any, Dict

from .base import MachineInterface


class CNCLatheInterface(MachineInterface):
    """Provides an interface for the CNC Lathe (Ecoca)"""
    @staticmethod
    def _poll_machine() -> Dict[Any, str]:
        """Polls CNC Lathe for data

        Returns
        -------
        Dict[Any, str]
            machine data gotten from CNC lathe hardware interface
        """
        # blah
        return {}
