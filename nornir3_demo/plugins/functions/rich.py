from nornir.core.task import AggregatedResult

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.box import MINIMAL_DOUBLE_HEAD


def build_report(results: AggregatedResult) -> None:
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
