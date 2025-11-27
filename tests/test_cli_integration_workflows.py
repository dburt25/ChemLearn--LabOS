import json
import subprocess
import sys
from pathlib import Path


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "labos.cli.main", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_lists_modules_via_workflow_registry():
    result = _run_cli(["job", "run", "--module", "pchem.calorimetry", "--operation", "compute", "--params", "{}"])
    assert result.returncode == 0, result.stderr

    registry_output = subprocess.run(
        [
            sys.executable,
            "-c",
            "from labos.modules import get_registry; print('\\n'.join(get_registry()._modules))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert registry_output.returncode == 0
    assert "pchem.calorimetry" in registry_output.stdout
    assert "ei_ms.basic_analysis" in registry_output.stdout


def test_cli_runs_calorimetry_with_params_file(tmp_path: Path):
    params = {"delta_t": 1.2, "heat_capacity": 4.18, "sample_id": "CLI-STUB"}
    params_file = tmp_path / "calorimetry_params.json"
    params_file.write_text(json.dumps(params), encoding="utf-8")

    result = _run_cli(
        [
            "job",
            "run",
            "--module",
            "pchem.calorimetry",
            "--operation",
            "compute",
            "--params",
            params_file.read_text(encoding="utf-8"),
        ]
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["succeeded"] is True
    assert payload["module_output"]["module_key"] == "pchem.calorimetry"
    assert "dataset" in payload["module_output"]
    assert payload["job"]["kind"] == "pchem.calorimetry:compute"
