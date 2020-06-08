#!/usr/bin/env python

from typing import List, Optional

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.rich import RichTable
from nornir3_demo.plugins.functions.rich import build_report

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
    nr_with_rich_table = nr.with_processors([RichTable(total_hosts)])
    results = nr_with_rich_table.run(task=upgrade_os, version=version)

    print()
    print("Task completed!!!")
    while True:
        print("Build report? [y/n] ", end="")
        user_input = input()
        if user_input == "y":
            build_report(results)
            break
        elif user_input == "n":
            print()
            break


if __name__ == "__main__":
    main()
