# LabOS CLI Quickstart

The minimal LabOS command-line interface focuses on two workflows: creating
experiments and running module-backed jobs. Commands bridge directly to the
workflow helpers in `labos.core.workflows`, so results mirror the same models
used elsewhere in LabOS.

## Commands

### Create an experiment

```bash
labos experiment create --name "Kinetic sweep" --owner chemist-1
```

- Generates an experiment identifier (e.g., `EXP-202...`).
- Accepts optional `--mode`, `--status`, and `--metadata` flags to align with
  `ExperimentMode`/`ExperimentStatus`.

### Run a module job

```bash
labos job run --module demo.calorimetry --params '{"temp": 298}'
```

- Executes the registered module operation via `run_module_job`.
- Returns a JSON payload containing experiment, job, dataset, and audit event
  records for quick scripting and debugging.
- Optional flags let you override the experiment name, owner, and mode if the
  command needs to mint a new experiment on the fly.

## Examples with custom parameters

```bash
labos experiment create --name "Spectroscopy baseline" --metadata '{"instrument": "FTIR"}'
labos job run --module demo.spectroscopy --operation simulate --params '{"wavelength": 650}' --actor cli.user
```
