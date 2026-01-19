"""Helmert similarity transform solver and residuals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class HelmertTransform:
    scale: float
    rotation: np.ndarray
    translation: np.ndarray

    def as_matrix(self) -> np.ndarray:
        matrix = np.eye(4)
        matrix[:3, :3] = self.scale * self.rotation
        matrix[:3, 3] = self.translation
        return matrix

    def inverse(self) -> "HelmertTransform":
        inv_scale = 1.0 / self.scale
        inv_rotation = self.rotation.T
        inv_translation = -inv_scale * (inv_rotation @ self.translation)
        return HelmertTransform(inv_scale, inv_rotation, inv_translation)

    def apply(self, points: np.ndarray) -> np.ndarray:
        return (self.scale * (self.rotation @ points.T)).T + self.translation


@dataclass(frozen=True)
class ResidualReport:
    per_point_m: list[float]
    rmse_m: float
    mean_m: float
    p95_m: float


def solve_helmert(model_points: Sequence[Sequence[float]], world_points: Sequence[Sequence[float]]) -> HelmertTransform:
    model = np.asarray(model_points, dtype=float)
    world = np.asarray(world_points, dtype=float)
    if model.shape != world.shape:
        raise ValueError("Model and world points must have the same shape.")
    if model.shape[0] < 3:
        raise ValueError("At least 3 GCPs are required to solve a Helmert transform.")

    centered = model - model.mean(axis=0)
    if np.linalg.matrix_rank(centered) < 2:
        raise ValueError("GCPs are collinear; provide non-collinear points.")

    model_mean = model.mean(axis=0)
    world_mean = world.mean(axis=0)
    model_centered = model - model_mean
    world_centered = world - world_mean

    covariance = model_centered.T @ world_centered
    u, s, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T

    scale = float(np.sum(s) / np.sum(model_centered**2))
    translation = world_mean - scale * (rotation @ model_mean)

    return HelmertTransform(scale=scale, rotation=rotation, translation=translation)


def compute_residuals(transform: HelmertTransform, model_points: Sequence[Sequence[float]], world_points: Sequence[Sequence[float]]) -> ResidualReport:
    model = np.asarray(model_points, dtype=float)
    world = np.asarray(world_points, dtype=float)
    transformed = transform.apply(model)
    errors = np.linalg.norm(transformed - world, axis=1)
    rmse = float(np.sqrt(np.mean(errors**2)))
    mean = float(np.mean(errors))
    p95 = float(np.percentile(errors, 95))
    return ResidualReport(per_point_m=errors.tolist(), rmse_m=rmse, mean_m=mean, p95_m=p95)


def to_homogeneous(points: Iterable[Sequence[float]]) -> np.ndarray:
    pts = np.asarray(list(points), dtype=float)
    ones = np.ones((pts.shape[0], 1))
    return np.hstack([pts, ones])
