import time
import random

from typing import Dict, Optional


class ConnectionException(Exception):
    pass


def maybe_fail(max_latency: int, chance_of_error: int = 1000) -> None:
    # simulate latency
    time.sleep(random.randint(1, 200) / 100)

    #  simulate random network errors
    if random.randint(1, chance_of_error) < 10:
        raise ConnectionException("problem communicating with device")


class AcmeOSAPI:
    def __init__(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
    ) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

        minor_version = random.randint(1, 4)
        revision = random.randint(0, 9) if minor_version != 4 else 1
        self.version = f"5.{minor_version}.{revision}"

    def open(self) -> None:
        maybe_fail(1)

    def close(self) -> None:
        maybe_fail(1)

    def _process_version(self, version: str) -> Dict[str, str]:
        ver = version.split(".")
        if len(ver) != 3:
            raise ValueError(
                "version format isn't correct, it should be in the format X.Y.Z"
            )
        return {
            "os_version": ".".join(ver[:2]),
            "revision": ver[2],
            "full_version": version,
        }

    def get_version(self) -> Dict[str, str]:
        maybe_fail(10)
        return self._process_version(self.version)

    def get_cpu_ram(self) -> Dict[str, int]:
        maybe_fail(10)
        return {
            "cpu": random.randint(10, 50),
            "ram_total": 4096,
            "ram_used": random.randint(1024, 2048),
        }

    def install_os_version(self, version: str) -> Dict[str, str]:
        maybe_fail(100, 500)

        result = self._process_version(version)
        self.version = version
        return result
