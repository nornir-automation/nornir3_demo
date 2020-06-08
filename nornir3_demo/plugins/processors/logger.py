import uuid

from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Task


import logging


class Logger:
    def __init__(self, filename: str, log_level: int = logging.INFO) -> None:
        self.logger = logging.getLogger("nornir_runner_logger")

        handler = logging.FileHandler(filename=filename)
        formatter = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
        handler.setFormatter(formatter)

        self.logger.setLevel(log_level)

        self.logger.addHandler(handler)

    def task_started(self, task: Task) -> None:
        # we generate a unique uuid and attach it to all the logs
        # this unique uuid will allow us to correlate logs and filter them by task execution
        self.uuid = uuid.uuid4()
        self.logger.info("%s:starting  task:%s", self.uuid, task.name)

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        self.logger.info("%s:completed task:%s", self.uuid, task.name)

    def task_instance_started(self, task: Task, host: Host) -> None:
        self.logger.info("%s:starting  host:%s", self.uuid, task.host.name)

    def task_instance_completed(
        self, task: Task, host: Host, results: MultiResult
    ) -> None:
        if results.failed:
            self.logger.error(
                "%s:completed host:%s:%s",
                self.uuid,
                task.host.name,
                results[-1].exception,
            )
        else:
            self.logger.info(
                "%s:completed host:%s:%s", self.uuid, task.host.name, results.result
            )

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        self.logger.debug(
            "%s:starting  subtask:%s:%s", self.uuid, task.host.name, task.name
        )

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        if result.failed:
            self.logger.error(
                "%s:completed subtask:%s:%s:%s",
                self.uuid,
                task.host.name,
                task.name,
                result.exception,
            )
        else:
            self.logger.debug(
                "%s:completed subtas:%s:%s:%s",
                self.uuid,
                task.host.name,
                task.name,
                result.result,
            )
