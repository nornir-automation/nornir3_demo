#!/usr/bin/env python

from nornir import InitNornir

from nornir3_demo.plugins.processors.rich import ProgressBar
from nornir3_demo.plugins.runners.dc_aware import DCAwareRunner
from nornir3_demo.plugins.tasks import acmeos

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

dc_runner = DCAwareRunner(num_workers=100)

nr = nr.with_processors([ProgressBar(total_hosts)]).with_runner(dc_runner)

nr.run(task=acmeos.upgrade_os, version="5.3.1")


# let's print the report so we can see which hosts failed and which ones were skipped
print()
for data in dc_runner.report():
    print(data)
