#!/usr/bin/env python

from typing import List, Optional

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.rich import RichTable
from nornir3_demo.plugins.functions.rich import build_report

from nornir.core.task import Task


def gather_info(task: Task) -> None:
    task.run(task=acmeos.get_version)
    task.run(task=acmeos.get_cpu_ram)


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

    total_hosts = len(nr.inventory.hosts)
    nr_with_rich_table = nr.with_processors([RichTable(total_hosts)])
    results = nr_with_rich_table.run(task=gather_info)
    build_report(results)


if __name__ == "__main__":
    main()
