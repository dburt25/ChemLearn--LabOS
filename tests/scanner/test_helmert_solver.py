import numpy as np
import pytest

from src.scanner.geo.helmert import compute_residuals, solve_helmert


def _build_transform(scale: float, rotation: np.ndarray, translation: np.ndarray, points: np.ndarray) -> np.ndarray:
    return (scale * (rotation @ points.T)).T + translation


def test_helmert_solver_recovers_transform() -> None:
    rng = np.random.default_rng(42)
    points = rng.normal(size=(10, 3))
    rotation = np.array(
        [
            [0.0, -1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    scale = 2.5
    translation = np.array([1.0, -2.0, 0.5])
    world = _build_transform(scale, rotation, translation, points)

    transform = solve_helmert(points, world)

    assert np.isclose(transform.scale, scale, atol=1e-6)
    assert np.allclose(transform.rotation, rotation, atol=1e-6)
    assert np.allclose(transform.translation, translation, atol=1e-6)


def test_helmert_solver_reports_residuals() -> None:
    rng = np.random.default_rng(123)
    points = rng.normal(size=(8, 3))
    rotation = np.eye(3)
    scale = 1.2
    translation = np.array([-1.0, 0.3, 2.0])
    noise = rng.normal(scale=0.01, size=points.shape)
    world = _build_transform(scale, rotation, translation, points) + noise

    transform = solve_helmert(points, world)
    residuals = compute_residuals(transform, points, world)

    assert residuals.rmse_m > 0
    assert len(residuals.per_point_m) == len(points)


def test_helmert_solver_rejects_too_few_points() -> None:
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="At least 3"):
        solve_helmert(points, points)


def test_helmert_solver_rejects_collinear_points() -> None:
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="collinear"):
        solve_helmert(points, points)
