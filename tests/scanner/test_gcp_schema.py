import numpy as np
import pytest

from src.scanner.geo.gcp import ENUOrigin, geodetic_to_enu, load_gcps


def test_load_gcps_local(tmp_path) -> None:
    content = """id,model_x,model_y,model_z,world_x,world_y,world_z
p1,0,0,0,10,20,30
p2,1,2,3,11,21,31
p3,2,2,2,12,22,32
"""
    gcp_path = tmp_path / "gcp.csv"
    gcp_path.write_text(content)

    gcp_set = load_gcps(gcp_path)

    assert gcp_set.world_frame == "local"
    assert gcp_set.enu_origin is None
    assert gcp_set.model_points.shape == (3, 3)
    assert gcp_set.world_points.shape == (3, 3)


def test_load_gcps_geodetic(tmp_path) -> None:
    content = """id,model_x,model_y,model_z,lat,lon,alt_m
p1,0,0,0,37.0,-122.0,10
p2,1,0,0,37.0001,-122.0,10
p3,0,1,0,37.0,-122.0001,10
"""
    gcp_path = tmp_path / "gcp.csv"
    gcp_path.write_text(content)

    gcp_set = load_gcps(gcp_path)

    assert gcp_set.world_frame == "enu"
    assert gcp_set.enu_origin is not None
    assert np.isfinite(gcp_set.world_points).all()


def test_geodetic_to_enu_finite() -> None:
    origin = ENUOrigin(
        lat_deg=37.0,
        lon_deg=-122.0,
        alt_m=10.0,
        ecef=np.array([1.0, 1.0, 1.0]),
        rotation=np.eye(3),
    )
    enu = geodetic_to_enu(37.0, -122.0, 10.0, origin)
    assert enu.shape == (3,)
    assert np.isfinite(enu).all()


def test_load_gcps_requires_world(tmp_path) -> None:
    content = """id,model_x,model_y,model_z
p1,0,0,0
"""
    gcp_path = tmp_path / "gcp.csv"
    gcp_path.write_text(content)

    with pytest.raises(ValueError, match="world_x/y/z or lat/lon/alt_m"):
        load_gcps(gcp_path)
