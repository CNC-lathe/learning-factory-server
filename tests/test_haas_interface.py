from typing import Any, Dict, Tuple
import copy
import random
import pickle
import string
import time
import threading
import unittest

import zmq

from lf_utils import retry

class MockHaasInterface():
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        super().__init__(*args, **kwargs)

        self._return_machine_data = False
        self._wait_interval = 0.01