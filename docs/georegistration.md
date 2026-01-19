# Georegistration (GEOREG v1)

This repository implements a first-pass **georegistration** workflow using Ground Control Points (GCPs). The goal is to solve a **3D similarity transform** (scale + rotation + translation), also known as a Helmert transform, that maps model coordinates from reconstruction space into a world coordinate frame.

## What is a similarity transform?
A similarity transform preserves shape by applying:

- **Scale** `s` (uniform)
- **Rotation** `R` (3×3 orthonormal)
- **Translation** `t`

The forward mapping is:

```
X_world = s * R * X_model + t
```

This is the backbone for absolute claims, because it aligns the reconstruction to real-world coordinates.

## GCP input formats
GCPs must include both model and world coordinates. Supported CSV schemas:

### Local metric coordinates
```
id,model_x,model_y,model_z,world_x,world_y,world_z
```

### Geodetic coordinates
```
id,model_x,model_y,model_z,lat,lon,alt_m
```

If geodetic coordinates are supplied, they are converted into a **local ENU (East, North, Up)** frame using the **first GCP as the ENU origin**. The ENU origin (lat/lon/alt) is recorded in `out/geo/geo_transform.json`.

## Interpreting residuals
Residuals are computed after solving the Helmert transform:

- Per-point error magnitude (meters)
- RMSE (meters)
- Mean residual (meters)
- p95 residual (meters)

Residuals are written to `out/geo/gcp_residuals.json` and summarized in `stage_reports/georeg.json`. There are **no accuracy claims** beyond the measured residuals.

## Outputs
Successful georegistration writes:

- `out/geo/geo_transform.json`
- `out/geo/gcp_residuals.json`
- `out/transforms.json` updated with `T_georeg`
- Georegistered copies of reconstruction artifacts:
  - `out/reconstruction/sparse_georeg.ply`
  - `out/reconstruction/dense_georeg.ply` (if present)
  - `out/reconstruction/mesh_georeg.obj` (if present)

Original reconstruction outputs are never overwritten.

## Absolute eligibility (AERIAL_ABS)
A run can be **eligible** for absolute claims only when:

1. It is already REL eligible.
2. Georegistration was solved successfully.
3. RMSE is below the configured threshold (default: **0.05 m**).

Even when eligible, `claim_level_absolute` remains **UNVERIFIED** unless external ground-truth verification is provided separately.

## CLI flags
The georegistration CLI supports the following flags:

- `--georeg {off,on,require}` (default: `off`)
- `--gcp-file <path>` (required if georeg is `on` or `require`)
- `--georeg-space {raw,scaled,centered,anchored}` (default: `anchored`)
- `--georeg-max-rmse-m <float>` (default: `0.05`)

These flags select the model coordinate space to solve in, and the RMSE threshold used for ABS eligibility gating.

## Manual GCP collection (v1)
For now, GCPs are collected manually by measuring recognizable control points and pairing them with reconstruction model coordinates. Use at least **three non-collinear GCPs**, ideally more, and ensure they are well distributed spatially.

This georegistration step is the first absolute backbone for future ABS claims, with every claim grounded in measured residuals rather than assumptions.
