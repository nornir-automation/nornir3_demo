---
---

{{% section %}}
## Functions

A nornir function is a standard python function you invoke on your own

There are no rules to write them :)

`print_result` is the most well known example of a nornir function

---

### Example: rich_table

We are going to write an alternative to `print_result` that leverages [rich](https://github.com/willmcgugan/rich)

---

``` python
# nornir3_demo/plugins/functions/rich.py
def rich_table(results: AggregatedResult) -> None:
    console = Console()

    for hostname, host_result in results.items():
        table = Table(box=MINIMAL_DOUBLE_HEAD)
        table.add_column(hostname, justify="right", style="cyan", no_wrap=True)
        table.add_column("result")
        table.add_column("changed")

        for r in host_result:
            text = Text()
            if r.failed:
                text.append(f"{r.exception}", style="red")
            else:
                text.append(f"{r.result or ''}", style="green")

            changed = Text()
            if r.changed:
                color = "orange3"
            else:
                color = "green"
            changed.append(f"{r.changed}", style=color)
            table.add_row(r.name, text, changed)
        console.print(table)
```

---

Script:

``` python
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
```

---

Output:

{{< figure src="img/rich_table.png" alt="rich table" width="70%" >}}

---

### Example: dcaware report

In the previous section we built a `DCAwareRunner`. This runner returned a report indicating which hosts failed and which ones were skipped and why. We are going to build a function that processes that report and builds a nice table.


---

``` python
def rich_dc_aware_report(dc_runner: DCAwareRunner) -> Table:
    table = Table(box=MINIMAL_DOUBLE_HEAD, title="DCAwareRunner report")
    table.add_column("group", justify="right", style="blue", no_wrap=True)
    table.add_column("failed", style="red")
    table.add_column("skipped", style="sky_blue3")
    table.add_column("error")

    for group_name, failed, skipped, exc in dc_runner.report():
        failed_hosts = ", ".join([h.name for h in failed])
        skipped_hosts = ", ".join([h.name for h in skipped])
        table.add_row(group_name, failed_hosts, skipped_hosts, f"{exc}")

    return table
```

---

### Example: dcaware report

Script:

``` python
# demo/scripts/51_dc_aware_runner_report.py

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
```

---

Output:

{{< figure src="img/rich_report.png" alt="progress bar" width="90%" >}}

---

### Questions so far?

{{% /section %}}
