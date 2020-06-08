from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Task

from rich.progress import Progress, BarColumn


class RichTable:
    def __init__(self, total: int) -> None:
        self.progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.completed:>3.0f}/{task.total}",
        )
        self.total = self.progress.add_task("[cyan]Completed...", total=total)
        self.successful = self.progress.add_task("[green]Successful...", total=total)
        self.changed = self.progress.add_task("[orange3]Changed...", total=total)
        self.error = self.progress.add_task("[red]Failed...", total=total)

    def task_started(self, task: Task) -> None:
        self.progress.start()

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        self.progress.stop()

    def task_instance_started(self, task: Task, host: Host) -> None:
        pass

    def task_instance_completed(
        self, task: Task, host: Host, results: MultiResult
    ) -> None:
        self.progress.update(self.total, advance=1)
        if results.failed:
            self.progress.update(self.error, advance=1)
        else:
            self.progress.update(self.successful, advance=1)
        if results.changed:
            self.progress.update(self.changed, advance=1)

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        pass

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        pass
