from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Task

from rich.progress import Progress, BarColumn


class ProgressBar:
    def __init__(self, total: int) -> None:
        # we will need to inform this processor the total amount of hosts
        # we instantiate a progress bar object
        self.progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.completed:>3.0f}/{task.total}",
        )

        # we create four progress bars to track total execution, successes, errors and changes
        self.total = self.progress.add_task("[cyan]Completed...", total=total)
        self.successful = self.progress.add_task("[green]Successful...", total=total)
        self.changed = self.progress.add_task("[orange3]Changed...", total=total)
        self.error = self.progress.add_task("[red]Failed...", total=total)

    def task_started(self, task: Task) -> None:
        # we start the progress bar
        self.progress.start()

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        # we stop the progress bar
        self.progress.stop()

    def task_instance_started(self, task: Task, host: Host) -> None:
        pass

    def task_instance_completed(
        self, task: Task, host: Host, results: MultiResult
    ) -> None:
        # we upgrade total execution advancing 1
        self.progress.update(self.total, advance=1)
        if results.failed:
            # if the task failed we increase the progress bar counting errors
            self.progress.update(self.error, advance=1)
        else:
            # if the task succeeded we increase the progress bar counting successes
            self.progress.update(self.successful, advance=1)

        if results.changed:
            # if the task changed the device we increase the progress bar counting changes
            self.progress.update(self.changed, advance=1)

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        pass

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        pass
