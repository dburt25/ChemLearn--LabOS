"""Reference frame centering for scanner reconstructions."""

from __future__ import annotations

from typing import Any

from scanner.anchors import AnchorResult, Confidence


def apply_reference_frame(
    reconstruction: dict[str, Any],
    metadata: dict[str, Any],
    anchor_result: AnchorResult | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "origin_xyz": None,
        "source": None,
        "notes": [],
    }

    if anchor_result and anchor_result.origin_xyz is not None:
        if anchor_result.confidence != Confidence.LOW:
            result["origin_xyz"] = anchor_result.origin_xyz
            result["source"] = "anchor"
            result["notes"].append("Applied anchor-derived origin.")
            return result
        result["notes"].append("Anchor origin ignored due to low confidence.")

    fallback_origin = metadata.get("origin_xyz")
    if fallback_origin is not None:
        result["origin_xyz"] = fallback_origin
        result["source"] = "metadata"
        result["notes"].append("Applied metadata origin fallback.")

    return result
