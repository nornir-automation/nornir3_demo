import logging

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.logger import Logger
from nornir3_demo.plugins.processors.rich import ProgressBar

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

# We can run as many procressors at the same time as we want!!!
nr_with_progress_bar_and_logs = nr.with_processors(
    [ProgressBar(total_hosts), Logger("upgrade_os.log", log_level=logging.DEBUG)]
)

nr_with_progress_bar_and_logs.run(task=acmeos.upgrade_os, version="5.3.2")
