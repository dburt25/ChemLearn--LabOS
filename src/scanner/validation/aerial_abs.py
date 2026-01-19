"""Absolute eligibility gating based on georegistration residuals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbsoluteEligibility:
    abs_eligible: bool
    claim_level_absolute: str
    reason: str
    rel_eligible: bool
    georeg_solved: bool
    rmse_m: float | None
    max_rmse_m: float


def evaluate_aerial_abs(
    *,
    rel_eligible: bool,
    georeg_solved: bool,
    rmse_m: float | None,
    max_rmse_m: float,
) -> dict:
    if not rel_eligible:
        return AbsoluteEligibility(
            abs_eligible=False,
            claim_level_absolute="UNVERIFIED",
            reason="REL not eligible",
            rel_eligible=rel_eligible,
            georeg_solved=georeg_solved,
            rmse_m=rmse_m,
            max_rmse_m=max_rmse_m,
        ).__dict__
    if not georeg_solved:
        return AbsoluteEligibility(
            abs_eligible=False,
            claim_level_absolute="UNVERIFIED",
            reason="georegistration not solved",
            rel_eligible=rel_eligible,
            georeg_solved=georeg_solved,
            rmse_m=rmse_m,
            max_rmse_m=max_rmse_m,
        ).__dict__
    if rmse_m is None:
        return AbsoluteEligibility(
            abs_eligible=False,
            claim_level_absolute="UNVERIFIED",
            reason="missing RMSE",
            rel_eligible=rel_eligible,
            georeg_solved=georeg_solved,
            rmse_m=rmse_m,
            max_rmse_m=max_rmse_m,
        ).__dict__
    if rmse_m > max_rmse_m:
        return AbsoluteEligibility(
            abs_eligible=False,
            claim_level_absolute="UNVERIFIED",
            reason=f"RMSE {rmse_m:.4f} exceeds threshold",
            rel_eligible=rel_eligible,
            georeg_solved=georeg_solved,
            rmse_m=rmse_m,
            max_rmse_m=max_rmse_m,
        ).__dict__
    return AbsoluteEligibility(
        abs_eligible=True,
        claim_level_absolute="UNVERIFIED",
        reason="georeg RMSE within threshold",
        rel_eligible=rel_eligible,
        georeg_solved=georeg_solved,
        rmse_m=rmse_m,
        max_rmse_m=max_rmse_m,
    ).__dict__
