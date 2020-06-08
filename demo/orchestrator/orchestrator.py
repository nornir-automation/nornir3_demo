#!/usr/bin/env python

import json
import logging
from typing import Any, Dict, List, Optional

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import AggregatedResult

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.prometheus import Prometheus
from nornir3_demo.plugins.processors.logger import Logger
from nornir3_demo.plugins.runners.dc_aware import DCAwareRunner

from flask import Flask, Response, request

import prometheus_client

import ruamel.yaml

app = Flask(__name__)


prometheus = Prometheus()


@app.route("/swagger/")
def swagger() -> Response:
    """
    Serves the spec so we can use the swagger-ui
    """
    with open("swagger.yaml", "r") as f:
        yml = ruamel.yaml.YAML()
        spec_data = yml.load(f)
    return respond(spec_data)


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


def get_nornir(
    filter_sites: Optional[List[str]], filter_dev_types: Optional[List[str]]
) -> Nornir:
    processors = [prometheus, Logger("orchestrator.log", log_level=logging.INFO)]

    return InitNornir(
        inventory={
            "plugin": "ACMEInventory",
            "options": {
                "filter_sites": filter_sites,
                "filter_dev_types": filter_dev_types,
            },
        },
        runner={"plugin": "DCAwareRunner", "options": {"num_workers": 100}},
    ).with_processors(processors)


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


@app.route("/metrics/")
def metrics() -> Response:
    CONTENT_TYPE_LATEST = str("text/plain; version=0.0.4; charset=utf-8")
    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/upgrade-os/", methods=["POST"])
def upgrade_os_endpoint() -> Response:
    nr = get_nornir(
        request.json.get("filter_sites"), request.json.get("filter_dev_types")
    )
    version = request.json["version"]

    results = nr.run(task=acmeos.upgrade_os, version=version)

    report = calculate_result(nr.runner, results)

    return respond(report)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
