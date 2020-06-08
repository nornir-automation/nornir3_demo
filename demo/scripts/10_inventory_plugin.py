from pprint import pprint

from nornir import InitNornir

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

pprint(nr.inventory.groups)

pprint(nr.inventory.hosts)
