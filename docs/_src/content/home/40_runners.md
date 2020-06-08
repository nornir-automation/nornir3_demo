---
---

{{% section %}}

## Runners

A runner is a plugin that dictates how to execute the tasks over the hosts

---

Nornir comes with two runners:

* **`SerialRunner`** executes the task over all the hosts one after the other
* **`ThreadedRunner`** executes the task over all the hosts in parallel using threads (default)

---

You can implement a runner by writing a class with the following structure:


``` python
class DCAwareRunner:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # This method will allow you to configure the plugin
        # For instance, when creating the object runner.options will be passed
        # to this constructor
        ...

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        # here is where you would implement your logic to "spread" the task over the hosts
```
---

## Registering the runner

As with the `InventoryPlugin` and the `ConnectionPlugin` we need to register the runner. We can do it in two ways:

1. Using [entrypoints](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)
2. Programmatically

---

### Registering Runner Plugins using Entrypoints

Add to your `setup.py`:

``` python
setup(
    # ...
    entry_points={
      "nornir.plugins.runners": "runner_name = path.to:RunnerPlugin",
    }
)
```

Or if using poetry, add to `pyproject.toml`:

``` toml
[tool.poetry.plugins."nornir.plugins.runners"]
"runner_name" = "path.to:RunnerPlugin"
```

* **`runner_name`** is the name of the runner, you will refer to this plugin by this name when writing tasks
* **`path.to:RunnerPlugin`** is the path to the class implementing the plugin

---

### Example: DCAwareRunner

As we have seen already Acme has 8 datacenters with 2 edge devices, 4 spines and 50 racks with two ToRs each. The way the network is designed allows us to lose an edge device, a spine or even a ToR on each rack without impacting normal operations.

---

To perform operations at scale in our network we are going to design a runner that takes these properties into account. To do that we are going to do the following:

1. We are going to group our devices based on their redundancy group
2. Those groups will be independent between datacenters (i.e. losing an edge in dc A doesn't have an impact on dc B)
3. Those groups will be:
    1. One for all the edge devices
    2. One for all the spines
    3. One for each pair of ToRs
    4. This means each DC will have 50 ToR groups + 1 edge group + 1 spine group
4. We will parallelize all the groups but only one device of each group will be run at a time
5. If a device in a group fails, pending devices in the same group will NOT be executed


---

Code is not too complex but it's rather large so I'd encourage you to look at it directly on [github](https://github.com/nornir-automation/nornir3_demo/blob/master/nornir3_demo/plugins/runners/dc_aware.py)


---

Now that we have the plugin, we need to register it. As we are using `poetry` in our project that's what we will use to register it:

``` toml
# pyproject.toml
...

[tool.poetry.plugins."nornir.plugins.runners"]
"DCAwareRunner" = "nornir3_demo.plugins.runners.dc_aware:DCAwareRunner"

...
```


---

### Demo: DCAwareRunner

Script:

``` python
from nornir import InitNornir

from nornir3_demo.plugins.processors.rich import ProgressBar
from nornir3_demo.plugins.runners import DCAwareRunner
from nornir3_demo.plugins.tasks import acmeos

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

total_hosts = len(nr.inventory.hosts)
nr = nr.with_processors([ProgressBar(total_hosts)])

dc_runner = DCAwareRunner(num_workers=100)
nr = nr.with_runner(dc_runner)

nr.run(task=acmeos.upgrade_os, version="5.3.1")

# let's print the report so we can see which hosts failed and which ones were skipped
print()
for data in dc_runner.report():
    print(data)
```
---

Output:

{{< figure src="img/dc_aware.png" alt="dc aware" >}}

A few notes:

1. You can see how the "Completed" progress bar didn't reach the end due to skipped hosts
2. In the report you can see "group_name", "failed_hosts", "skipped_hosts", "error"
3. Notice how when even devices (i.e. leaf32.mercury) failed, the even device was skipped
4. However, if the odd device failed, the even wasn't skipped. This is because the even device was executed before the odd one


---

### with_runner vs configuration

In the example we chose the runner with the following code:

``` python
dc_runner = DCAwareRunner(num_workers=100)
nr = nr.with_runner(dc_runner)
```

This allows you to set up the runner "at runtime", but you can also configure it like this if you prefer:

``` python
nr = InitNornir(
    runner={
        "plugin": "DCAwareRunner",
        "options": {
            "num_workers": 100,
        },
    },
)
```

You can choose one method or the other depending on your needs

---

### Questions so far?

{{% /section %}}
