from nornir.core.task import Result, Task

from nornir3_demo.plugins.connections.acmeos import CONNECTION_NAME


def get_version(task: Task) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    return Result(host=task.host, result=device.get_version())


def get_cpu_ram(task: Task) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    return Result(host=task.host, result=device.get_cpu_ram())


def install_os_version(task: Task, version: str) -> Result:
    device = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    return Result(
        host=task.host, result=device.install_os_version(version), changed=True
    )


def upgrade_os(task: Task, version: str) -> Result:
    result = task.run(task=get_version)
    if result.result["full_version"] == version:
        return Result(host=task.host, changed=False, result="nothing to do!!!")
    task.run(task=install_os_version, version=version)
    return Result(host=task.host, changed=True, result="success!!!")
