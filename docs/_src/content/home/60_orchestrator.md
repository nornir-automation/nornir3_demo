---
---

{{% section %}}

## Orchestrator

Finally we are going to wrap everything up by writing a POC for an orchestraor

It won't be feature complete but it will highlight its capabilities

---

## Objective and Steps

* Write a HTTP API that allows us to execute tasks over our network
* To showcase the orchestrator we will have an endpoint that will upgrade the OS in our entire network leveraging everything we built so far
* We will use flask to write the service
* We will write an [OpenAPI specification](https://swagger.io/)
* Finally we will add some instrumentation

---

## OpenAPI Specification

The specification can be found under [orchestrator.yaml](https://github.com/nornir-automation/nornir3_demo/blob/master/demo/orchestrator/swagger.yaml)

Let's start by writing and endpoint to serve it so we can usee the swagger-ui

---


``` python
def respond(raw: Any) -> Response:
    """
    This methods serializes the response into json and
    set the appropiate HTTP headers
    """
    return Response(
        json.dumps(raw),
        status=200,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # this is certainly not good in prod!!!
            "Access-Control-Allow-Methods": "GET, POST, DELETE, PUT, PATCH, OPTIONS",
        },
    )

@app.route("/swagger/")
def swagger() -> Response:
    """
    Serves the spec so we can use the swagger-ui
    """
    with open("swagger.yaml", "r") as f:
        yml = ruamel.yaml.YAML()
        spec_data = yml.load(f)
    return respond(spec_data)
```


---

We can start the orchestrar so far with:

``` sh
$ cd demo/orchestrator
$ python orchestrator.py
 * Serving Flask app "orchestrator" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

Now we can start `swagger-ui`:

``` sh
docker run --rm -p 8080:8080 swaggerapi/swagger-ui
```

---

With everything up and running we can go to the URL [http://localhost:8080](http://localhost:8080) and enter the URL to explore `http://localhost:5000/swagger/`

---

{{< figure src="img/swagger_1.png" alt="swagger 1" width="90%" >}}

---

{{< figure src="img/swagger_2.png" alt="swagger 2" width="90%" >}}

---

{{< figure src="img/swagger_3.png" alt="swagger 3" width="90%" >}}

---

Now let's implement the endpoint

---

Let's start by writing a method that will return the nornir object fully configured:

``` python
prometheus = Prometheus()

def get_nornir(
    filter_sites: Optional[List[str]], filter_dev_types: Optional[List[str]]
) -> Nornir:
    processors = [prometheus, Logger("orchestrator.log", log_level=logging.INFO)]

    return InitNornir(
        inventory={
            "plugin": "ACMEInventory",
            "options": {
                "filter_dev_types": filter_dev_types,
                "filter_sites": filter_sites,
            },
        },
        runner={
            "plugin": "DCAwareRunner",
            "options": {"num_workers": 100}},
    ).with_processors(processors)

```

Note: We will get back to the `Prometheus()` processor later on.

---

Now we need to return a dictionary with the `completed`, `failed` and `skipped` hosts. That information will come from the `AggregatedResult` and `DCAwareRunner` report so let's write a function to generate this response:


``` python
def calculate_result(
    dc_runner: DCAwareRunner, results: AggregatedResult
) -> Dict[str, List[str]]:
    report: Dict[str, List[str]] = {
        "failed": [],
        "skipped": [],
        "completed": [h for h, r in results.items() if not r.failed],
    }
    for _, failed, skipped, _ in dc_runner.report():
        report["failed"].extend([h.name for h in failed])
        report["skipped"].extend([h.name for h in skipped])

    return report
```
---

Finally, our endpoint is going to be just a few lines as we leverage everything we wrote so far:

``` python
@app.route("/upgrade-os/", methods=["POST"])
def upgrade_os_endpoint() -> Response:
    nr = get_nornir(
        request.json.get("filter_sites"), request.json.get("filter_dev_types")
    )
    version = request.json["version"]

    results = nr.run(task=acmeos.upgrade_os, version=version)

    report = calculate_result(nr.runner, results)

    return respond(report)
```

---

Let's try it out!

``` sh
$ curl -X POST \
  -H "Content-Type: application/json" \
  -d "{  \"version\": \"5.3.1\",  \"filter_dev_sites\": [\"earth\"]}" \
  http://localhost:5000/upgrade-os/ | jq  # use jq to make the output slightly prettier
{
  "failed": [
    "leaf63.earth",
    "leaf81.earth",
    "leaf92.earth",
    "leaf98.earth"
  ],
  "skipped": [
    "leaf93.earth",
    "leaf99.earth"
  ],
  "completed": [
    "edge00.earth",
    "edge01.earth",
    "spine00.earth",
    "spine01.earth",
    "spine02.earth",
    "spine03.earth"
    ...
  ]
}
```

---

We could run other sites or devices types if we wanted too:

``` sh
$ curl -X POST \
  -H "Content-Type: application/json" \
  -d "{\"version\": \"5.3.1\", \"filter_dev_types\": [\"spine\"]}" \
  http://localhost:5000/upgrade-os/ | jq  # use jq to make the output slightly prettier
{
  "failed": [
    "spine00.mars"
  ],
  "skipped": [
    "spine01.mars",
    "spine02.mars",
    "spine03.mars"
  ],
  "completed": [
    "spine00.mercury",
    "spine00.venus",
    "spine00.earth",
    "spine00.jupyter",
    "spine00.uranus",
    ...
  ]
}
```

---

Finally we are going to add some observability metrics to our system. To do so we are going to use the `Prometheus` processor you already saw in the `get_nornir` method.

The prometheus processor will count successes, changes and failures so we can graph them over time.

---

``` python
# nornir3_demo/plugins/processors/prometheus.py
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
```

---

``` python
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

    def subtask_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        pass
```

---

Now we add an endpoint to our orchestrator to expose these metrics:

``` python
@app.route("/metrics/")
def metrics() -> Response:
    CONTENT_TYPE_LATEST = str("text/plain; version=0.0.4; charset=utf-8")
    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)

```

---

Let's try it:

``` sh
$ curl http://localhost:5000/metrics/
...
total_task_requests_per_host_total{dev_type="spine",host="spine03.jupyter",site="jupyter"} 3.0
total_task_requests_per_host_total{dev_type="spine",host="spine03.uranus",site="uranus"} 3.0
total_task_requests_per_host_total{dev_type="spine",host="spine03.saturn",site="saturn"} 2.0
total_task_requests_per_host_total{dev_type="spine",host="spine03.neptune",site="neptune"} 2.0
...
failed_tasks_per_host_total{dev_type="spine",host="spine03.uranus",site="uranus"} 1.0
failed_tasks_per_host_total{dev_type="spine",host="spine01.saturn",site="saturn"} 1.0
failed_tasks_per_host_total{dev_type="spine",host="spine02.neptune",site="neptune"} 1.0
...
```

---

Now you could have prometheus gather this metrics, create dashboard with grafana, and see how the systems behaves over time!

---

### Questions so far?

{{% /section %}}
