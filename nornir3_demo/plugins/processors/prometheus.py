from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Task

from prometheus_client import Counter


class Prometheus:
    def __init__(self) -> None:
        self.total_task_requests = Counter(
            "total_task_requests", "Total number of task requests"
        )
        self.failed_tasks = Counter("failed_tasks", "Total number of task requests")
        self.total_tasks_per_host = Counter(
            "total_task_requests_per_host",
            "Total number of task requests per host",
            ["host", "site", "dev_type"],
        )
        self.failed_tasks_per_host = Counter(
            "failed_tasks_per_host",
            "Total number of task requests per host",
            ["host", "site", "dev_type"],
        )

    def task_started(self, task: Task) -> None:
        self.total_task_requests.inc()

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        if result.failed:
            self.failed_tasks.inc()

    def task_instance_started(self, task: Task, host: Host) -> None:
        self.total_tasks_per_host.labels(
            task.host.name, task.host.data["site"], task.host.data["dev_type"]
        ).inc()

    def task_instance_completed(
        self, task: Task, host: Host, results: MultiResult
    ) -> None:
        if results.failed:
            self.failed_tasks_per_host.labels(
                task.host.name, task.host.data["site"], task.host.data["dev_type"]
            ).inc()

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        pass

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        pass
