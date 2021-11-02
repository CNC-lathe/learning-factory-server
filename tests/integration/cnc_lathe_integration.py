import time
from unittest import mock

from server.machine_interfaces.cnc_lathe import CNCLatheInterface
from server.machine_interfaces import MachineInterface


def create_interface(uuid: str, port: int, fail_hard: bool):
    patcher = mock.patch.object(MachineInterface, "__init__", mock.Mock)
    with patcher:
        patcher.is_local = True
        interface = CNCLatheInterface(
            None, {"bt_params": {"uuid": uuid, "port": port}, "fail_hard": fail_hard}
        )

    return interface


def main(uuid: str, port: int, fail_hard: bool, update_interval: float):
    lathe = create_interface(uuid, port, fail_hard)

    print()
    step = 0
    while True:
        print(f"Step: {step} || {lathe._poll_machine()}", end="\r")
        time.sleep(update_interval)
        step += 1

    
if __name__ == "__main__":

    import argparse
    
    parser = argparse.ArgumentParser(description="Tests CNC lathe interface.")
    parser.add_argument("--uuid", default="00:14:03:05:08:53")
    parser.add_argument("--port", default=1, type=int)
    parser.add_argument("--update_interval", default=1.0, type=float)
    parser.add_argument("--fail_hard", action="store_true")

    args = parser.parse_args()

    main(args.uuid, args.port, args.fail_hard, args.update_interval)
