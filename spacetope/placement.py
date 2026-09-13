"""A placement assigns an integer-mm Box to every space. Intent can be derived from it."""
from __future__ import annotations

import json
from pathlib import Path

from .brief import Brief
from .solve.grid import Box, contact_area, intersects, overlap_len, OPPOSITE
from .spacegraph import AssemblyGraph, Contact, HORIZONTAL_SIDES, SIDES

Placement = dict[str, Box]


def load_placement(path: str | Path) -> Placement:
    d = json.loads(Path(path).read_text())
    return {name: Box.from_dict(b) for name, b in d["boxes"].items()}


def save_placement(placement: Placement, path: str | Path, brief_name: str = "") -> None:
    Path(path).write_text(json.dumps(
        {"brief": brief_name, "boxes": {n: b.to_dict() for n, b in placement.items()}}, indent=2))


def check_complete(brief: Brief, placement: Placement) -> None:
    missing = {s.name for s in brief.spaces} - set(placement)
    extra = set(placement) - {s.name for s in brief.spaces}
    if missing or extra:
        raise ValueError(f"placement/brief mismatch: missing={sorted(missing)} extra={sorted(extra)}")


def assembly_from_placement(brief: Brief, placement: Placement, min_area_mm2: int = 1) -> AssemblyGraph:
    """Every face-coincident pair with positive overlap becomes a contact edge (intent = geometry)."""
    check_complete(brief, placement)
    ag = AssemblyGraph(brief)
    names = list(placement)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for side in SIDES:
                if contact_area(placement[a], placement[b], side) >= min_area_mm2:
                    ag.add_contact(a, side, b, OPPOSITE[side])
    return ag


def diagnose_contact(c: Contact, placement: Placement, gap_limit_mm: int = 100) -> str:
    """Why a contact is not realised in this placement: 'ok' | 'gap' | 'overlap' | 'missing'."""
    a, b = placement[c.a], placement[c.b]
    if contact_area(a, b, c.side_a) > 0:
        return "ok"
    if intersects(a, b):
        return "overlap"
    axis, ca = a.face_plane(c.side_a)
    _, cb = b.face_plane(c.side_b)
    in_plane = [ax for ax in "xyz" if ax != axis]
    lateral = all(overlap_len(a.interval(ax), b.interval(ax)) > 0 for ax in in_plane)
    if lateral and 0 < abs(ca - cb) <= gap_limit_mm:
        return "gap"
    return "missing"


def overlaps(placement: Placement) -> list[tuple[str, str]]:
    names = list(placement)
    return [(a, b) for i, a in enumerate(names) for b in names[i + 1:] if intersects(placement[a], placement[b])]
