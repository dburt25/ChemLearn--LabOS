"""Shared helpers for LabOS Streamlit views."""

from __future__ import annotations

from typing import Mapping, Sequence, cast

from labos.jobs import Job


def extract_dataset_ids(job: Job) -> list[str]:
    """Extract dataset identifiers from a job's parameters.

    This keeps UI surfaces in sync with how dataset references are represented
    on ``Job`` records without reaching into private registry internals.
    """

    ids: list[str] = []
    params_obj = getattr(job, "parameters", None)
    if not isinstance(params_obj, Mapping):
        return ids

    parameters = cast(Mapping[str, object], params_obj)

    maybe_many = parameters.get("dataset_ids")
    if isinstance(maybe_many, Sequence) and not isinstance(maybe_many, (str, bytes, bytearray)):
        ids.extend(str(item) for item in cast(Sequence[object], maybe_many))

    maybe_one = parameters.get("dataset_id")
    if maybe_one is not None:
        ids.append(str(maybe_one))

    return list(dict.fromkeys(ids))
