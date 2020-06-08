---
---

{{% section %}}
## Connection plugins

A connection plugin is a nornir plugin that allows nornir to manage connections with devices

---

It is implemented by writing a class with the following structure:

``` python
from typing import Any, Dict, Optional

from nornir.core.configuration import Config


CONNECTION_NAME = "my-connection-name"


class MyPlugin:
    def open(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        # we open the connection and save it under self.connection
        self.connection = connection

    def close(self) -> None:
        # logic to close the connection
```


---

## Registering the connection plugin

As with the `InventoryPlugin` we need to register the connection plugin. We can do it in two ways:

1. Using [entrypoints](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)
2. Programmatically

---

### Registering Connection Plugins using Entrypoints

Add to your `setup.py`:

``` python
setup(
    # ...
    entry_points={
      "nornir.plugins.connections": "connection_name = path.to:ConnectionPlugin",
    }
)
```

Or if using poetry, add to `pyproject.toml`:

``` toml
[tool.poetry.plugins."nornir.plugins.connections"]
"connection_name" = "path.to:ConnectionPlugin"
```

* **`connection_name`** is the name of the connection, you will refer to this plugin by this name when writing tasks
* **`path.to:ConnectionPlugin`** is the path to the class implementing the plugin

---

### Registering Connection Plugins Programmatically


``` python
from nornir.core.plugins.connections import ConnectionPluginRegister

from path.to import ConnectionPlugin


ConnectionPluginRegister.register("connection-name", ConnectionPlugin)

```

---

## Example: AcmeOS Connection Plugin

Our AcmeOS device has a python library we can leverage. In order to manage the connection to the device it provides a constructor and two methods:

* `AcmeOS(hostname, username, password, port)` - Create an instance of the object to interact with a device
* `open()` - Establishes a connection
* `close()` - Closes the connection

---

``` python
# nornir3_demo/plugins/connections/acmeos.py

# we will pretend this library was given to us by a third party
from nornir3_demo.ext.acmeos import AcmeOSAPI


# We will use this variable in the tasks to quickly reference the plugin
CONNECTION_NAME = "acmeos"


class AcmeOS:
    def open(...) -> None:
        # we use the constructor to pass the parameters needed by the library
        connection = AcmeOSAPI(hostname, username, password, port)

        # now we call the open method as instructed by the library documentation
        connection.open()

        # finally we save the connection under self.connection as instructed by nornir
        self.connection = connection

    def close(self) -> None:
        # we follow the instructions provided by the library to close the connection
        self.connection.close()
```

---

Now that we have the plugin, we need to register it. As we are using `poetry` in our project that's what we will use to register it:

``` toml
# pyproject.toml
...

[tool.poetry.plugins."nornir.plugins.connections"]
"acmeos" = "nornir3_demo.plugins.connections.acmeos:AcmeOS"

...
```


---

Now we are ready to write a few tasks that will leverage this connection plugin.

Let's start by looking at the vendor's documentation, according to it we have a few methods that are interesting to us:

* **`get_version()`** - Returns a dictionary with OS information
* **`get_cpu_ram()`** - Returns a dictionary with information about cpu and ram usage
* **`install_os_version(version: str)`** - Installs the given version of the device's operating system

---


``` python
# nornir3_demo/plugins/tasks/acmeos/__init__.py

from nornir.core.task import Result, Task

# We import the CONNECTION_NAME from the plugin itself
from nornir3_demo.plugins.connections.acmeos import CONNECTION_NAME


def get_version(task: Task) -> Result:
    # nornir manages the connection automatically using the Connection plugin
    # To retrieve it you can just call the following method. Note that
    # CONNETION_NAME needs to match the name we used when registering the plugin
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)

    # now we are ready to use the library given to us by the vendor
    version_info = device.get_version()

    return Result(host=task.host, result=version_info)

```

---

``` python
# nornir3_demo/plugins/tasks/acmeos/__init__.py
#
# continuation...

def get_cpu_ram(task: Task) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    return Result(host=task.host, result=device.get_cpu_ram())


def install_os_version(task: Task, version: str) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)

    # note that we set changed=True as we changed the system
    return Result(
        host=task.host, result=device.install_os_version(version), changed=True
    )
```

---

``` python
# nornir3_demo/plugins/tasks/acmeos/__init__.py
#
# continuation...

def upgrade_os(task: Task, version: str) -> Result:
    # we use task get_verion to retrieve current OS running
    result = task.run(task=get_version)

    # if the version matches what we want to install we are done!
    if result.result["full_version"] == version:
        return Result(host=task.host, result="nothing to do!!!")

    # otherwise we call install_os_version task to install the image
    task.run(task=install_os_version, version=version)
    return Result(host=task.host, changed=True, result="success!!!")
```

---

## Demo: AcmeOS Connection Plugin

---

Script:

``` python
# demo/scripts/20_connection_plugin.py
from nornir import InitNornir

from nornir3_demo.plugins.tasks import acmeos

nr = InitNornir(
    inventory={"plugin": "ACMEInventory", "options": {"filter_sites": ["earth"]}}
)


results = nr.run(task=acmeos.get_version)

for hostname, result in results.items():
    if result.failed:
        print(f"{hostname}: {result.exception}")
    else:
        print(f"{hostname}: {result.result['full_version']}")
```

Output:

``` sh
$ python 20_connection_plugin.py
edge00.earth: problem communicating with device
edge01.earth: 5.4.1
spine00.earth: 5.2.1
spine01.earth: 5.2.4
spine02.earth: 5.1.3
spine03.earth: 5.2.9
leaf00.earth: 5.2.3
leaf01.earth: 5.4.1
leaf02.earth: 5.2.7
...
```

---

### Questions so far?

{{% /section %}}
