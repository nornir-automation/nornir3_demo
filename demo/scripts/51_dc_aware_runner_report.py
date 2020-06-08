#!/usr/bin/env python

from nornir import InitNornir

from nornir3_demo.plugins.processors.rich import ProgressBar
from nornir3_demo.plugins.runners.dc_aware import DCAwareRunner
from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.functions.rich import rich_dc_aware_report

from rich.console import Console

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

dc_runner = DCAwareRunner(num_workers=100)

nr = nr.with_processors([ProgressBar(total_hosts)]).with_runner(dc_runner)

nr.run(task=acmeos.upgrade_os, version="5.3.1")

table = rich_dc_aware_report(dc_runner)
Console().print("\n", table)
