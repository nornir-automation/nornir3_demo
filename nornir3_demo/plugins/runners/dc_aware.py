import time
from typing import Dict, Iterator, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD

from nornir.core.task import AggregatedResult, Task
from nornir.core.inventory import Host


class DeviceGroups:
    """
    We use device groups to group devices by their "redundancy domain"

    Only one host failure per device group is tolerated so if a device
    fails we will skip pending devices
    """

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
        """
        we only consider pending devices if no other host has failed
        """
        return len(self.pending_hosts) > 0 and len(self.failed_hosts) == 0

    def complete(self) -> None:
        """
        when completing a host we move the host from in_progress to completed_hosts
        """
        self.completed_hosts.append(self.in_progress)
        self.in_progress = None

    def fail(self, exc: Exception) -> None:
        """
        when a host fails we move it from in_progress to failed_hosts
        this will cause pending to return false
        we also save the exception we got
        """
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


class Root(Dict[str, DeviceGroups]):
    """
    This object will serve as root for all the device groups independently
    from the DC they belong to
    """

    def pending(self) -> bool:
        """
        We will return true of any device group has pending hosts
        """
        return any([dg.pending() for dg in self.values()])

    def batch(self) -> Iterator[Host]:
        """
        Everytime this method is called we will go through all the device groups,
        check if they are ready (no other host is running) and if they have
        pending devices, in which, case we will yield it
        """
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
        """
        This method will iterateover all the  return a dictionary with the list of completed, failed
        and skipped hostt for all the device groups
        """
        for group_name, dg in self.items():
            if dg.failed_hosts or dg.pending_hosts:
                yield dg.name, dg.failed_hosts, dg.pending_hosts, dg.error or Exception(
                    "unknown"
                )


def sort_hosts(hosts: List[Host]) -> Root:
    """
    This method helps sorting hosts for a given DC, it will create the corresponding
    device groups and assign the hosts to them
    """
    root = Root()
    for host in hosts:
        group_name = get_group_name(host)

        if group_name not in root:
            root[group_name] = DeviceGroups(group_name)

        root[group_name].append(host)

    return root


class DCAwareRunner:
    """
    ThreadedRunner runs the task over each host using threads

    Arguments:
        num_workers: number of threads to use
    """

    def __init__(self, num_workers: int = 20) -> None:
        self.num_workers = num_workers
        self.oor = Root()

    def report(self) -> Iterator[Tuple[str, List[Host], List[Host], Exception]]:
        """
        Iterate over all the device groups and return their report
        """
        return self.root.report()

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        """
        This is where the magic happens
        """

        # first we create the root object with all the device groups in it
        self.root = sort_hosts(hosts)

        # we instantiate the aggregated result
        result = AggregatedResult(task.name)

        # when sending the tasks to the pool we will store the futures here
        futures = []

        with ThreadPoolExecutor(self.num_workers) as pool:
            while self.root.pending():
                # for as long as we have pending objects

                # we execute the task over a batch of devices and store
                # the futures
                for host in self.root.batch():
                    future = pool.submit(task.copy().start, host)
                    futures.append(future)

                # we process the futures
                while futures:
                    future = futures.pop(0)
                    worker_result = future.result()
                    result[worker_result.host.name] = worker_result
                    if worker_result.failed:
                        self.root.fail(worker_result.host, worker_result[-1].exception)
                    else:
                        self.root.complete(worker_result.host)
                time.sleep(1)

        return result
