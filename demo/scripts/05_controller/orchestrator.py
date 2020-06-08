#!/usr/bin/env python

import json
import logging
from typing import Any, Dict, List

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import AggregatedResult

from nornir3_demo.plugins.tasks import acmeos
from nornir3_demo.plugins.processors.prometheus import Prometheus
from nornir3_demo.plugins.processors.logger import Logger
from nornir3_demo.plugins.runners import DCAwareRunner

from flask import Flask, Response, request

import prometheus_client

import ruamel.yaml

app = Flask(__name__)
processors = [Prometheus(), Logger("orchestrator.log", log_level=logging.INFO)]


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


def get_nornir() -> Nornir:
    nr = InitNornir(
        inventory={
            "plugin": "ACMEInventory",
            "options": {
                #  "filter_dev_types": filter_dev_types,
                "filter_sites": ["earth"],
            },
        }
    )
    return nr


def respond(raw: Any) -> Response:
    return Response(
        json.dumps(raw),
        status=200,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, PUT, PATCH, OPTIONS",
        },
    )


@app.route("/swagger/")
def swagger() -> Response:
    with open("swagger.yaml", "r") as f:
        yml = ruamel.yaml.YAML()
        spec_data = yml.load(f)
    return respond(spec_data)


@app.route("/metrics/")
def metrics() -> Response:
    CONTENT_TYPE_LATEST = str("text/plain; version=0.0.4; charset=utf-8")
    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/upgrade-os/", methods=["POST"])
def upgrade_os_endpoint() -> Response:
    print(request.json)
    nr = get_nornir()
    version = "5.4.1"

    dc_runner = DCAwareRunner(num_workers=100)

    nr = nr.with_processors(processors).with_runner(dc_runner)

    results = nr.run(task=acmeos.upgrade_os, version=version)

    report = calculate_result(dc_runner, results)

    return respond(report)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
