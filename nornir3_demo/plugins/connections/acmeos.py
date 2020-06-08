from typing import Any, Dict, Optional

from nornir.core.configuration import Config
from nornir.core.connections import ConnectionPlugin

from nornir3_demo.ext.acmeos import AcmeOSAPI


CONNECTION_NAME = "acmeos"


class AcmeOS(ConnectionPlugin):
    def open(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        connection = AcmeOSAPI(hostname, username, password, port)
        connection.open()
        self.connection = connection

    def close(self) -> None:
        self.connection.close()
