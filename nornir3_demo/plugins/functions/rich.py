from nornir.core.task import AggregatedResult

from nornir3_demo.plugins.runners.dc_aware import DCAwareRunner

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.box import MINIMAL_DOUBLE_HEAD


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
