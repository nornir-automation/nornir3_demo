#!/usr/bin/env python

from typing import List, Optional

from rich.console import Console

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.rich import RichTable
from nornir3_demo.plugins.runners import DCAwareRunner, rich_dc_aware_report

from nornir.core.task import Task, Result


def upgrade_os(task: Task, version: str) -> Result:
    result = task.run(task=acmeos.get_version)
    if result.result["full_version"] == version:
        return Result(host=task.host, changed=False)
    task.run(task=acmeos.install_os_version, version=version)
    return Result(host=task.host, changed=True)


def main(
    filter_dev_types: Optional[List[str]] = None,
    filter_sites: Optional[List[str]] = None,
) -> None:
    nr = InitNornir(
        inventory={
            "plugin": "ACMEInventory",
            "options": {
                "filter_dev_types": filter_dev_types,
                "filter_sites": filter_sites,
            },
        }
    )
    version = "5.4.1"

    total_hosts = len(nr.inventory.hosts)

    dc_runner = DCAwareRunner(num_workers=100)

    nr = nr.with_processors([RichTable(total_hosts)]).with_runner(dc_runner)
    nr.run(task=upgrade_os, version=version)

    console = Console()
    console.print()
    console.print(rich_dc_aware_report(dc_runner))


if __name__ == "__main__":
    main()
