from nornir import InitNornir

nr = InitNornir(
    inventory={
        "plugin": "ACMEInventory",
        "options": {"filter_sites": ["earth"], "filter_dev_types": ["spine", "edge"]},
    }
)

print(nr.inventory.groups)

print(nr.inventory.hosts)
