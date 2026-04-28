"""
Post-process LLM `joint_angles` before OpenSim pose + *_coords.mot generation.

Fills missing distal interphalangeal (DIP) flexion from proximal interphalangeal (PIP)
when the model expects both but the LLM often omits DIP (defaults to 0 otherwise).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# (PIP coordinate, DIP coordinate) for Gonzalez-style hand naming
PIP_DIP_CHAINS: List[Tuple[str, str]] = [
    ("PIP_flex", "DIP_flex"),
    ("MPIP_flex", "MDIP_flex"),
    ("RPIP_flex", "RDIP_flex"),
    ("LPIP_flex", "LDIP_flex"),
]

# If PIP is flexed at least this much (deg), treat DIP as "should match" when missing/zero
_MIN_PIP_TO_PROPAGATE_DEG = 15.0


def augment_joint_angles(
    joint_angles: Dict[str, float],
    model_coord_names: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Return a new dict with DIP angles filled from PIP where appropriate.

    Rules (per finger chain):
    - If DIP is missing, or DIP is 0 while PIP suggests flexion (>= _MIN_PIP_TO_PROPAGATE_DEG),
      set DIP = min(|PIP|, 90°).
    - If `model_coord_names` is given, only set coordinates that exist on the model.
    """
    out = {k: float(v) for k, v in joint_angles.items()}

    allowed = set(model_coord_names) if model_coord_names else None

    for pip_key, dip_key in PIP_DIP_CHAINS:
        if allowed is not None and dip_key not in allowed:
            continue
        if pip_key not in out:
            continue

        try:
            pip_val = float(out[pip_key])
        except (TypeError, ValueError):
            continue

        if abs(pip_val) < _MIN_PIP_TO_PROPAGATE_DEG:
            continue

        dip_missing = dip_key not in out
        try:
            dip_val = float(out.get(dip_key, 0.0))
        except (TypeError, ValueError):
            dip_val = 0.0

        if dip_missing or dip_val == 0.0:
            out[dip_key] = min(abs(pip_val), 90.0)

    return out
