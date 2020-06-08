---
---

{{% section %}}
## Inventory plugins

An inventory plugin is a nornir plugin that allows nornir to create an `Inventory` object from an external source

---

It is implemented by writing a class with the following structure:

``` python
from typing import Dict, Optional, List

from nornir.core.inventory import Inventory

class MyPlugin:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # This method will allow you to configure the plugin
        # For instance, when creating the object inventory.options will be passed
        # to this constructor
        ...

    def load(self) -> Inventory:
        # This method will be called and it will be responsible to instantiate and
        # return the Inventory
        ...
```

---

## Registering the Inventory plugin

In order for nornir to be able to use the inventory plugin we need to register it. You can do so in two ways:

1. Using [entrypoints](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)
2. Programmatically

---

### Registering Inventory Plugins using Entry Points

Add to your `setup.py`:

``` python
setup(
    # ...
    entry_points={
      "nornir.plugins.inventory": "inventory-name = path.to:InventoryPlugin",
    }
)
```

Or if using poetry, add to `pyproject.toml`:

``` toml
[tool.poetry.plugins."nornir.plugins.inventory"]
"inventory-name" = "path.to:InventoryPlugin"
```

* **`inventory_name`** is the name of the inventory, you will refer to this plugin by this name in the `inventory.plugin` configuration option in `config.yaml` or when calling `InitNornir`
* **`path.to:InventoryPlugin`** is the path to the class implementing the plugin

---

### Registering Inventory Plugins Programmatically


``` python
from nornir.core.plugins.inventory import InventoryPluginRegister

from path.to import InventoryPlugin


InventoryPluginRegister.register("inventory-name", InventoryPlugin)

```

---

## Example: Acme's Inventory Plugin

We are using as inventory ACME's inventory system. In order to interact with it we could use `requests` or some other library, however, we have been given already a library that interacts with the backend so we are going to leverage it.

Looking at the documentation given to us by the developer of the library we care about the following methods:

* `ACMEAPI()` - Create an instance of the object to interact with the inventory. Takes no arguments.
* `get(filter_sites: Optional[List[str]] = None, filter_dev_types: Optional[List[str]] = None)` - Returns information about all of our hosts spread across all of our datacenters. This method takes an optional list of sites and an optional list of device types to help us filter the inventory.

---

Let's start by trying the library in the console:

``` python
$ ipython
In [1]: from nornir3_demo.ext.inventory import ACMEAPI
In [2]: acme = ACMEAPI()
In [3]: acme.get()
Out[3]:
{'mercury': {'edge00.mercury': {'platform': 'acmeos',
   'dev_type': 'edge',
   'rack': '10'},
  'edge01.mercury': {'platform': 'acmeos', 'dev_type': 'edge', 'rack': '10'},
  'spine00.mercury': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '20'},
  'spine01.mercury': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '20'},
  'spine02.mercury': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '21'},
  'spine03.mercury': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '21'},
  'leaf00.mercury': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '100'},
  'leaf01.mercury': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '100'},

  ...

  'leaf94.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '147'},
  'leaf95.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '147'},
  'leaf96.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '148'},
  'leaf97.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '148'},
  'leaf98.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '149'},
  'leaf99.neptune': {'platform': 'acmeos', 'dev_type': 'leaf', 'rack': '149'}}}

```

---

Let's try the filtering capabilities:


``` python
In [4]: acme.get(filter_sites=["earth"], filter_dev_types=["edge", "spine"])
Out[4]:
{'earth': {'edge00.earth': {'platform': 'acmeos',
   'dev_type': 'edge',
   'rack': '10'},
  'edge01.earth': {'platform': 'acmeos', 'dev_type': 'edge', 'rack': '10'},
  'spine00.earth': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '20'},
  'spine01.earth': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '20'},
  'spine02.earth': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '21'},
  'spine03.earth': {'platform': 'acmeos', 'dev_type': 'spine', 'rack': '21'}}}
```

Turns out we have:

* 8 datacenters
* with:
  * 2 edge devices each
  * 4 spines each
  * 100 ToRs each

The inventory also give us some rack information

---

In order to write our inventory plugin we need to write a plugin that gets the data using the library that was given to us and applies the necessary transformations to create the inventory object.

Let's look at it step by step:

---


``` python
# nornir3_demo/plugins/inventory/acme.py

# we will pretend this library was given to us by a third party
from nornir3_demo.ext.inventory import ACMEAPI


class ACMEInventory:
    def __init__(
        self,
        filter_sites: Optional[List[str]] = None,
        filter_dev_types: Optional[List[str]] = None,
    ) -> None:
        # we will use the constructor to create the inventory object
        self.conn = ACMEAPI()

        # we will also save the parameters so we can use them later on
        self.filter_sites = filter_sites
        self.filter_dev_types = filter_dev_types

    ...
```

---

``` python
# nornir3_demo/plugins/inventory/acme.py
    ...

    def load(self) -> Inventory:
        # we retrieve the data from the inventory passing the options we saved
        # in he constructor
        data = self.conn.get(self.filter_sites, self.filter_dev_types)
        # we create placeholder for the hosts and for the groups
        hosts = Hosts()
        groups = Groups()

        # the inventory returned the hosts by datacenter so we iterate over them
        for dc_name, dc_data in data.items():
            # we are going to start by creating a group per DC
            groups[dc_name] = Group(dc_name)

            # now we process the dc data we got
            hosts_in_dc = process_dc_data(groups[dc_name], dc_data)

            # we add the hosts in the dc to the main hosts object
            hosts.update(hosts_in_dc)

        # we populate the inventory and return it
        # note our inventory doesn't support defaults so we just return an empty object
        return Inventory(hosts=hosts, groups=groups, defaults=Defaults())
```

---

``` python
# nornir3_demo/plugins/inventory/acme.py

def process_dc_data(group: Group, group_data: Dict[str, Dict[str, str]]) -> Hosts:
    """
    Arguments:
        group: Current group we are processing
        group_data: the data for the entire group as returned by the backend
    """
    # we create a placeholder for the hosts
    hosts = Hosts()

    # inside each datacenter we had a dictionary where the key was the hostname
    # and the data inside had some data about it, we iterate over the hosts
    for hostname, host_data in group_data.items():
        # for each host we create a Host object mapping it's required parameters
        # with the data we got
        hosts[hostname] = Host(
            name=hostname,
            hostname=hostname,
            platform=host_data.pop("platform"),
            groups=ParentGroups([group]),  # we add the DC group as a parent group
            data={"site": group.name, **host_data},  # extra data
        )
    return hosts
```

---

## Registering the Inventory Plugin

Now that we have the plugin, we need to register it. As we are using `poetry` in our project that's what we will use to register it:

``` toml
# pyproject.toml
...

[tool.poetry.plugins."nornir.plugins.inventory"]
"ACMEInventory" = "nornir3_demo.plugins.inventory.acme:ACMEInventory"

...
```

---

## Demo: Acme's Inventory Plugin

---

Script:

``` python
# demo/scripts/10_inventory_plugin.py
from pprint import pprint

from nornir import InitNornir

nr = InitNornir(inventory={"plugin": "ACMEInventory"})

pprint(nr.inventory.groups)

pprint(nr.inventory.hosts)
```

Output:

```sh
$ python 10_inventory_plugin.py
{'earth': Group: earth,
 'jupyter': Group: jupyter,
 'mars': Group: mars,
 'mercury': Group: mercury,
 'neptune': Group: neptune,
 ...
{'edge00.earth': Host: edge00.earth,
 'edge00.jupyter': Host: edge00.jupyter,
 'edge00.mars': Host: edge00.mars,
 'edge00.mercury': Host: edge00.mercury,
 ...
```

---

Script:

``` python
# demo/scripts/10_inventory_plugin_filter.py
from nornir import InitNornir

nr = InitNornir(
    inventory={
        "plugin": "ACMEInventory",
        "options": {
            "filter_sites": ["earth"],
            "filter_dev_types": ["spine", "edge"],
        },
    }
)

print(nr.inventory.groups)

print(nr.inventory.hosts)
```

Output:

```sh
$ python 10_inventory_plugin_filter.py
{'earth': Group: earth}
{'edge00.earth': Host: edge00.earth,
 'edge01.earth': Host: edge01.earth,
 'spine00.earth': Host: spine00.earth,
 'spine01.earth': Host: spine01.earth,
 'spine02.earth': Host: spine02.earth,
 'spine03.earth': Host: spine03.earth}
```

---

### Questions so far?

{{% /section %}}
