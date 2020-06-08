from typing import Dict, Optional, List

from nornir.core.inventory import (
    Inventory,
    Group,
    Groups,
    Host,
    Hosts,
    Defaults,
    ParentGroups,
)

from nornir3_demo.ext.inventory import ACMEAPI, InventoryDataType


def process_group(group: Group, group_data: Dict[str, Dict[str, str]]) -> Hosts:
    """
    Arguments:
        group: Current group we are processing
        group_data: the data for the entire group as returned by the backend
    """
    hosts = Hosts()
    for hostname, host_data in group_data.items():
        hosts[hostname] = Host(
            name=hostname,
            hostname=hostname,
            platform=host_data.pop("platform"),
            groups=ParentGroups([group]),
            data={"site": group.name, **host_data},
        )
    return hosts


class ACMEInventory:
    def __init__(
        self,
        filter_sites: Optional[List[str]] = None,
        filter_dev_types: Optional[List[str]] = None,
    ) -> None:
        self.conn = ACMEAPI()
        self.filter_sites = filter_sites
        self.filter_dev_types = filter_dev_types

    def load(self) -> Inventory:
        data = self.conn.get(self.filter_sites, self.filter_dev_types)
        return self.process_data(data)

    def process_data(self, data: InventoryDataType) -> Inventory:
        hosts = Hosts()
        groups = Groups()
        for group_name, group_data in data.items():
            groups[group_name] = Group(group_name)
            group_hosts = process_group(groups[group_name], group_data)
            hosts.update(group_hosts)

        return Inventory(hosts=hosts, groups=groups, defaults=Defaults())


if __name__ == "__main__":
    from pprint import pprint

    pprint(ACMEInventory(filter_sites=["earth", "mars"]).load().dict())
