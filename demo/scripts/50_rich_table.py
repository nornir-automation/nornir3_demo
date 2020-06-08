from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.functions.rich import rich_table

from nornir.core.task import Task


def gather_info(task: Task) -> None:
    task.run(task=acmeos.get_version)
    task.run(task=acmeos.get_cpu_ram)


nr = InitNornir(
    inventory={"plugin": "ACMEInventory", "options": {"filter_sites": ["earth"]}}
)

results = nr.run(task=gather_info)
rich_table(results)
