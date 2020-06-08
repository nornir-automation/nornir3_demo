from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos

nr = InitNornir(
    inventory={"plugin": "ACMEInventory", "options": {"filter_sites": ["earth"]}}
)

results = nr.run(task=acmeos.get_version)

for hostname, result in results.items():
    if result.failed:
        print(f"{hostname}: {result.exception}")
    else:
        print(f"{hostname}: {result.result['full_version']}")
