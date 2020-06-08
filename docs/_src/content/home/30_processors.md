---
---

{{% section %}}

## Processors

A processor is a plugin that taps into certain events and allows the user to execute arbitrary code on those events.

Those events are:

1. When a task starts or finishes
2. When a host starts executing the task or completes it
3. When a host starts executing a subtasks or completes it

---

The benefit of using a `Processor` is that the code for each event is called as they occur so you can execute arbitrary code without having to wait until the entire task is completed

---

It is implemented by writing a class with the following structure:

``` python
from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Task


class MyProcessorPlugin:
    def task_started(self, task: Task) -> None:
        ...

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        ...

    def task_instance_started(self, task: Task, host: Host) -> None:
        ...

    def task_instance_completed(self, task: Task, host: Host, results: MultiResult) -> None:
        ...

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        ...

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        ...
```

---

### Example: rich progress bar

ACME has +800 devices so we are going to write a progress bar that will shows the progress of the execution in real time while we wait for everything to complete

Note: this plugin leverages [rich](https://github.com/willmcgugan/rich)

---

``` python
# nornir3_demo/plugins/processors/rich.py

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
```

---

``` python
# nornir3_demo/plugins/processors/rich.py (continuation)

    def task_instance_started(self, task: Task, host: Host) -> None:
        pass

    def task_instance_completed(self, task: Task, host: Host, results: MultiResult) -> None:
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

    def subtask_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        pass
```

---

### Demo: rich progress bar


Script:

``` python
# demo/scripts/30_progress_bar.py

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.rich import ProgressBar

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

nr_with_progress_bar = nr.with_processors([ProgressBar(total_hosts)])

nr_with_progress_bar.run(task=acmeos.upgrade_os, version="5.3.2")
```

---

{{< figure src="img/progress_bar_1.png" alt="progress bar" width="60%" >}}

(a few seconds later)

{{< figure src="img/progress_bar_2.png" alt="progress bar" width="60%" >}}

(on completion)

{{< figure src="img/progress_bar_3.png" alt="progress bar" width="60%" >}}

---

### Example: custom logging

In addition to our fancy progress bar we are going to add a logging processor so we can inspect the execution as it happens. We are going to log to a file but ideally we'd be using this to a syslog server connected to a system like splunk, graylog or to an ELK stack.

---

``` python
# nornir3_demo/plugins/processors/logger.py

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
```

---

``` python
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
            self.logger.error("%s:completed host:%s:%s", self.uuid, task.host.name, results[-1].exception)
        else:
            self.logger.info(
                "%s:completed host:%s:%s", self.uuid, task.host.name, results.result
            )
```

---

``` python
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
                "%s:completed subtask:%s:%s:%s",
                self.uuid,
                task.host.name,
                task.name,
                result.result,
            )
```

---

Script:

``` python
import logging

from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.logger import Logger
from nornir3_demo.plugins.processors.rich import ProgressBar

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)

# We can run as many procressors at the same time as we want!!!
nr_with_progress_bar_and_logs = nr.with_processors(
    [ProgressBar(total_hosts), Logger("upgrade_os.log", log_level=logging.DEBUG)]
)

nr_with_progress_bar_and_logs.run(task=acmeos.upgrade_os, version="5.3.2")
```

---

Output while executing `python 31_progress_bar_and_logs.py`:

``` sh
$ tail -f upgrade_os.log
...
DEBUG:2020-06-09 20:23:10,331:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:edge00.earth:install_os_version
DEBUG:2020-06-09 20:23:10,406:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf90.venus:install_os_version:{'os_version': '5.3', 'revision': '2', 'full_version': '5.3.2'}
INFO:2020-06-09 20:23:10,406:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf90.venus:success!!!
INFO:2020-06-09 20:23:10,406:bd566653-13f4-47a6-8350-a98301cc9eef:starting  host:leaf04.earth
DEBUG:2020-06-09 20:23:10,406:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:leaf04.earth:get_version
DEBUG:2020-06-09 20:23:10,462:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf89.venus:install_os_version:{'os_version': '5.3', 'revision': '2', 'full_version': '5.3.2'}
INFO:2020-06-09 20:23:10,463:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf89.venus:success!!!
INFO:2020-06-09 20:23:10,463:bd566653-13f4-47a6-8350-a98301cc9eef:starting  host:leaf05.earth
DEBUG:2020-06-09 20:23:10,463:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:leaf05.earth:get_version
DEBUG:2020-06-09 20:23:10,521:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:edge01.earth:get_version:{'os_version': '5.1', 'revision': '5', 'full_version': '5.1.5'}
DEBUG:2020-06-09 20:23:10,521:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:edge01.earth:install_os_version
DEBUG:2020-06-09 20:23:10,560:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf95.venus:get_version:{'os_version': '5.2', 'revision': '7', 'full_version': '5.2.7'}
DEBUG:2020-06-09 20:23:10,560:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:leaf95.venus:install_os_version
DEBUG:2020-06-09 20:23:10,691:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf93.venus:get_version:{'os_version': '5.3', 'revision': '6', 'full_version': '5.3.6'}
DEBUG:2020-06-09 20:23:10,691:bd566653-13f4-47a6-8350-a98301cc9eef:starting  subtask:leaf93.venus:install_os_version
DEBUG:2020-06-09 20:23:10,715:bd566653-13f4-47a6-8350-a98301cc9eef:completed host:leaf87.venus:install_os_version:{'os_version': '5.3', 'revision': '2', 'full_version': '5.3.2'}
...
```

---

### Questions so far?

{{% /section %}}
