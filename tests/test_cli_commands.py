import json
import os
import re
import subprocess
import sys


def run_cli(args, *, env=None):
    cmd = [sys.executable, "-m", "labos", *args]
    return subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)


def test_cli_lists_modules():
    result = run_cli(["list-modules"])
    assert "pchem.calorimetry" in result.stdout
    assert "Constant-pressure" in result.stdout


def test_cli_lists_experiments(tmp_path):
    env = {**os.environ, "LABOS_ROOT": str(tmp_path)}
    run_cli(
        [
            "new-experiment",
            "--user",
            "student",
            "--title",
            "Week1",
            "--purpose",
            "Buffer prep",
        ],
        env=env,
    )

    listed = run_cli(["list-experiments"], env=env)
    assert "Week1" in listed.stdout
    assert re.search(r"^id\s+name\s+created", listed.stdout, re.MULTILINE)


def test_cli_lists_datasets(tmp_path):
    env = {**os.environ, "LABOS_ROOT": str(tmp_path)}
    registration = run_cli(
        [
            "register-dataset",
            "--owner",
            "student",
            "--dataset-type",
            "experimental",
            "--uri",
            "s3://placeholder",
        ],
        env=env,
    )

    dataset_id_match = re.search(r"Registered dataset (\S+)", registration.stdout)
    assert dataset_id_match, registration.stdout

    listed = run_cli(["list-datasets"], env=env)
    assert dataset_id_match.group(1) in listed.stdout


def test_cli_run_module_outputs_workflow_result():
    result = run_cli(
        [
            "run-module",
            "pchem.calorimetry",
            "--params-json",
            "{\"delta_t\": 2.5}",
        ]
    )
    payload = json.loads(result.stdout)
    assert payload["job"]["kind"].startswith("pchem.calorimetry")
    assert payload["module_output"]["dataset"]["metadata"]["module_key"] == "pchem.calorimetry"
