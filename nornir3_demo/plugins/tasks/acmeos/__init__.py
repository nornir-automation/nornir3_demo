from nornir.core.task import Result, Task

from nornir3_demo.plugins.connections.acmeos import CONNECTION_NAME


def get_version(task: Task) -> Result:
    # nornir manages the connection automatically using the Connection plugin
    # To retrieve it you can just call the following method. Note that
    # CONNETION_NAME needs to match the name we used when registering the plugin
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)

    # now we are ready to use the library given to us by the vendor
    version_info = device.get_version()

    return Result(host=task.host, result=version_info)


def get_cpu_ram(task: Task) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    return Result(host=task.host, result=device.get_cpu_ram())


def install_os_version(task: Task, version: str) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)

    # note that we set changed=True as we changed the system
    return Result(
        host=task.host, result=device.install_os_version(version), changed=True
    )


def upgrade_os(task: Task, version: str) -> Result:
    # we use task get_verion to retrieve current OS running
    result = task.run(task=get_version)

    # if the version matches what we want to install we are done!
    if result.result["full_version"] == version:
        return Result(host=task.host, result="nothing to do!!!")

    # otherwise we call install_os_version task to install the image
    task.run(task=install_os_version, version=version)
    return Result(host=task.host, changed=True, result="success!!!")
