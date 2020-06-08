#!/usr/bin/env python

from typing import List, Optional

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos


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

    result = nr.run(task=acmeos.get_version)

    for hostname, host_result in result.items():
        if host_result.failed:
            print(f"{hostname}: {host_result.exception}")
        else:
            print(f"{hostname}: {host_result[0].result['full_version']}")


if __name__ == "__main__":
    main()
