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

from nornir3_demo.ext.inventory import ACMEAPI


def process_dc_data(group: Group, group_data: Dict[str, Dict[str, str]]) -> Hosts:
    """
    Arguments:
        group: Current group we are processing
        group_data: the data for the entire group as returned by the backend
    """
    # we create a placeholder for the hosts
    hosts = Hosts()

    # inside each datacenter we had a dictionary where the key was the hostname
    # and the data inside had some data about it, we iterate over the hosts
    for hostname, host_data in group_data.items():
        # for each host we create a Host object mapping it's required parameters
        # with the data we got
        hosts[hostname] = Host(
            name=hostname,
            hostname=hostname,
            platform=host_data.pop("platform"),
            groups=ParentGroups([group]),  # we add the DC group as a parent group
            data={"site": group.name, **host_data},  # extra data
        )
    return hosts


class ACMEInventory:
    def __init__(
        self,
        filter_sites: Optional[List[str]] = None,
        filter_dev_types: Optional[List[str]] = None,
    ) -> None:
        # we will use the constructor to create the connection object
        self.conn = ACMEAPI()

        # we will also save the parameters so we can use them later on
        self.filter_sites = filter_sites
        self.filter_dev_types = filter_dev_types

    def load(self) -> Inventory:
        # we retrieve the data from the inventory passing the options we saved
        # in he constructor
        data = self.conn.get(self.filter_sites, self.filter_dev_types)

        # we create placeholder for the hosts and for the groups
        hosts = Hosts()
        groups = Groups()

        # the inventory returned the hosts by datacenter so we iterate over them
        for dc_name, dc_data in data.items():
            # we are going to start bt creating a group per DC
            groups[dc_name] = Group(dc_name)

            # now we process the dc data we got
            hosts_in_dc = process_dc_data(groups[dc_name], dc_data)

            # we add the hosts in the dc to the main hosts object
            hosts.update(hosts_in_dc)

        # we populate the inventory and return it
        # note our inventory doesn't support defaults so we just return
        # and empty object
        return Inventory(hosts=hosts, groups=groups, defaults=Defaults())
