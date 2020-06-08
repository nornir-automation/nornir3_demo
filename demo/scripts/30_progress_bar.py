from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.rich import ProgressBar

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

nr_with_progress_bar = nr.with_processors([ProgressBar(total_hosts)])

nr_with_progress_bar.run(task=acmeos.upgrade_os, version="5.3.2")
