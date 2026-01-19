"""Ground control point parsing and conversions."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

import numpy as np

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)


@dataclass(frozen=True)
class GCPRecord:
    gcp_id: str
    model: np.ndarray
    world: np.ndarray


@dataclass(frozen=True)
class GCPSet:
    records: List[GCPRecord]
    world_frame: str
    enu_origin: dict | None = None

    @property
    def model_points(self) -> np.ndarray:
        return np.vstack([rec.model for rec in self.records])

    @property
    def world_points(self) -> np.ndarray:
        return np.vstack([rec.world for rec in self.records])


@dataclass(frozen=True)
class ENUOrigin:
    lat_deg: float
    lon_deg: float
    alt_m: float
    ecef: np.ndarray
    rotation: np.ndarray


def _to_float(value: str, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {label}: {value!r}") from exc


def _geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    lat = np.deg2rad(lat_deg)
    lon = np.deg2rad(lon_deg)
    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_lon = np.sin(lon)
    cos_lon = np.cos(lon)

    n = WGS84_A / np.sqrt(1 - WGS84_E2 * sin_lat**2)
    x = (n + alt_m) * cos_lat * cos_lon
    y = (n + alt_m) * cos_lat * sin_lon
    z = (n * (1 - WGS84_E2) + alt_m) * sin_lat
    return np.array([x, y, z], dtype=float)


def _enu_rotation(lat_deg: float, lon_deg: float) -> np.ndarray:
    lat = np.deg2rad(lat_deg)
    lon = np.deg2rad(lon_deg)
    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_lon = np.sin(lon)
    cos_lon = np.cos(lon)

    return np.array(
        [
            [-sin_lon, cos_lon, 0.0],
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
            [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat],
        ],
        dtype=float,
    )


def _build_origin(lat_deg: float, lon_deg: float, alt_m: float) -> ENUOrigin:
    ecef = _geodetic_to_ecef(lat_deg, lon_deg, alt_m)
    rotation = _enu_rotation(lat_deg, lon_deg)
    return ENUOrigin(lat_deg=lat_deg, lon_deg=lon_deg, alt_m=alt_m, ecef=ecef, rotation=rotation)


def geodetic_to_enu(lat_deg: float, lon_deg: float, alt_m: float, origin: ENUOrigin) -> np.ndarray:
    ecef = _geodetic_to_ecef(lat_deg, lon_deg, alt_m)
    diff = ecef - origin.ecef
    return origin.rotation @ diff


def _has_columns(row: Mapping[str, str], columns: Iterable[str]) -> bool:
    return all(col in row and row[col] not in (None, "") for col in columns)


def _parse_model(row: Mapping[str, str]) -> np.ndarray:
    return np.array(
        [
            _to_float(row["model_x"], "model_x"),
            _to_float(row["model_y"], "model_y"),
            _to_float(row["model_z"], "model_z"),
        ],
        dtype=float,
    )


def _parse_local_world(row: Mapping[str, str]) -> np.ndarray:
    return np.array(
        [
            _to_float(row["world_x"], "world_x"),
            _to_float(row["world_y"], "world_y"),
            _to_float(row["world_z"], "world_z"),
        ],
        dtype=float,
    )


def _parse_geodetic(row: Mapping[str, str]) -> tuple[float, float, float]:
    return (
        _to_float(row["lat"], "lat"),
        _to_float(row["lon"], "lon"),
        _to_float(row["alt_m"], "alt_m"),
    )


def load_gcps(path: str | Path) -> GCPSet:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("GCP file is empty.")

    records: list[GCPRecord] = []
    enu_origin: ENUOrigin | None = None
    world_frame = "local"

    for row in rows:
        if not _has_columns(row, ["id", "model_x", "model_y", "model_z"]):
            raise ValueError("GCP rows must include id, model_x, model_y, model_z.")

        model = _parse_model(row)
        if _has_columns(row, ["world_x", "world_y", "world_z"]):
            world = _parse_local_world(row)
            world_frame = "local"
        elif _has_columns(row, ["lat", "lon", "alt_m"]):
            lat_deg, lon_deg, alt_m = _parse_geodetic(row)
            if enu_origin is None:
                enu_origin = _build_origin(lat_deg, lon_deg, alt_m)
            world = geodetic_to_enu(lat_deg, lon_deg, alt_m, enu_origin)
            world_frame = "enu"
        else:
            raise ValueError("GCP rows must include either world_x/y/z or lat/lon/alt_m.")

        records.append(GCPRecord(gcp_id=row["id"], model=model, world=world))

    origin_payload = None
    if enu_origin is not None:
        origin_payload = {
            "lat": enu_origin.lat_deg,
            "lon": enu_origin.lon_deg,
            "alt_m": enu_origin.alt_m,
        }

    return GCPSet(records=records, world_frame=world_frame, enu_origin=origin_payload)
