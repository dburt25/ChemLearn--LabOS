"""Scale constraint application for scanner reconstructions."""

from __future__ import annotations

from typing import Any

from scanner.anchors import AnchorResult, Confidence


def apply_scale_constraints(
    reconstruction: dict[str, Any],
    metadata: dict[str, Any],
    anchor_result: AnchorResult | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "scale_factor": None,
        "source": None,
        "notes": [],
    }

    if anchor_result and anchor_result.scale_factor is not None:
        if anchor_result.confidence != Confidence.LOW:
            result["scale_factor"] = anchor_result.scale_factor
            result["source"] = "anchor"
            result["notes"].append("Applied anchor-derived scale factor.")
            return result
        result["notes"].append("Anchor scale factor ignored due to low confidence.")

    fallback_scale = metadata.get("scale_factor")
    if fallback_scale is not None:
        result["scale_factor"] = fallback_scale
        result["source"] = "metadata"
        result["notes"].append("Applied metadata scale factor fallback.")

    return result
