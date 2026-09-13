"""M6 dataset: one JSON line per verified option. Enough to re-realise and re-verify every row
from stored coordinates (integrity), and to train proposal models on brief graph -> relations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..brief import Brief
from ..pipeline import Option
from ..placement import assembly_from_placement
from ..solve.grid import Box
from ..verify import verify


def option_row(brief: Brief, option: Option) -> dict:
    return {
        "brief": brief.to_dict(),
        "brief_graph": {"nodes": [{"name": s.name, "program": s.program, "w": s.w, "l": s.l, "h": s.h} for s in brief.spaces],
                        "required": [list(c) for c in brief.contacts]},
        "generator": option.generator,
        "seed": option.seed,
        "signature": [list(s) for s in option.signature],
        "placement": {n: b.to_dict() for n, b in option.placement.items()},
        "scores": option.scores,
    }


def write_rows(rows: Iterable[dict], path: str | Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
            n += 1
    return n


def read_rows(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def check_row(row: dict) -> tuple[bool, str]:
    """Re-realise and re-verify a stored row; its signature must be unchanged."""
    brief = Brief.from_dict(row["brief"])
    placement = {n: Box.from_dict(b) for n, b in row["placement"].items()}
    intent = assembly_from_placement(brief, placement)
    sig = [list(s) for s in intent.signature()]
    if sig != row["signature"]:
        return False, "signature changed"
    rep = verify(brief, placement, intent)
    if not rep.ok:
        return False, json.dumps({k: d for k, (p, d) in rep.checks.items() if not p})
    return True, "ok"
