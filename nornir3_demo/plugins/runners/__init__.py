import time
from typing import Dict, Iterator, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD

from nornir.core.task import AggregatedResult, Task
from nornir.core.inventory import Host


class DeviceGroups:
    def __init__(self, name: str) -> None:
        self.name = name
        self.pending_hosts: List[Host] = []
        self.completed_hosts: List[Host] = []
        self.failed_hosts: List[Host] = []
        self.in_progress: Optional[Host] = None
        self.error: Optional[Exception] = None

    def append(self, host: Host) -> None:
        self.pending_hosts.append(host)

    def next(self) -> Host:
        self.in_progress = self.pending_hosts.pop(0)
        return self.in_progress

    def ready(self) -> bool:
        return self.in_progress is None

    def pending(self) -> bool:
        return len(self.pending_hosts) > 0 and len(self.failed_hosts) == 0

    def complete(self) -> None:
        self.completed_hosts.append(self.in_progress)
        self.in_progress = None

    def fail(self, exc: Exception) -> None:
        self.failed_hosts.append(self.in_progress)
        self.error = exc
        self.in_progress = None


def get_group_name(host: Host) -> str:
    site = host.data["site"]
    dev_type = host.data["dev_type"]
    rack = host.data["rack"]

    if dev_type == "leaf":
        group_name = f"{site}_{dev_type}_{rack}"
    else:
        group_name = f"{site}_{dev_type}"
    return group_name


class DC(Dict[str, DeviceGroups]):
    def pending(self) -> bool:
        return any([dg.pending() for dg in self.values()])

    def batch(self) -> Host:
        for group_name, dg in self.items():
            if dg.ready() and dg.pending():
                yield dg.next()

    def complete(self, host: Host) -> None:
        group_name = get_group_name(host)
        self[group_name].complete()

    def fail(self, host: Host, exc: Exception) -> None:
        group_name = get_group_name(host)
        self[group_name].fail(exc)

    def report(self,) -> Iterator[Tuple[str, List[Host], List[Host], Exception]]:
        for group_name, dg in self.items():
            if dg.failed_hosts or dg.pending_hosts:
                yield dg.name, dg.failed_hosts, dg.pending_hosts, dg.error or Exception(
                    "unknown"
                )


def sort_hosts(hosts: List[Host]) -> DC:
    dc = DC()
    for host in hosts:
        group_name = get_group_name(host)

        if group_name not in dc:
            dc[group_name] = DeviceGroups(group_name)

        dc[group_name].append(host)

    return dc


class DCAwareRunner:
    """
    ThreadedRunner runs the task over each host using threads

    Arguments:
        num_workers: number of threads to use
    """

    def __init__(self, num_workers: int = 20) -> None:
        self.num_workers = num_workers
        self.dc = DC()

    def report(self) -> Iterator[Tuple[str, List[Host], List[Host], Exception]]:
        return self.dc.report()

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        self.dc = sort_hosts(hosts)
        result = AggregatedResult(task.name)
        futures = []

        with ThreadPoolExecutor(self.num_workers) as pool:
            while self.dc.pending():
                for host in self.dc.batch():
                    future = pool.submit(task.copy().start, host)
                    futures.append(future)

                while futures:
                    future = futures.pop(0)
                    worker_result = future.result()
                    result[worker_result.host.name] = worker_result
                    if worker_result.failed:
                        self.dc.fail(worker_result.host, worker_result[-1].exception)
                    else:
                        self.dc.complete(worker_result.host)
                time.sleep(1)

        return result


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
