"""Generate -> realise -> verify -> score -> rank. Produces Options and scoreboard rows."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .brief import Brief
from .placement import Placement, assembly_from_placement
from .realise import Realised
from .score import METRICS, score
from .verify import VerifyReport, verify


@dataclass
class Option:
    placement: Placement
    signature: tuple
    report: VerifyReport
    scores: dict[str, float] = field(default_factory=dict)
    generator: str = ""
    seed: int = 0

    @property
    def ok(self) -> bool:
        return self.report.ok

    @property
    def realised(self) -> Realised | None:
        return self.report.realised

    def to_dict(self) -> dict:
        return {"generator": self.generator, "seed": self.seed, "ok": self.ok, "scores": self.scores,
                "signature": [list(s) for s in self.signature],
                "placement": {n: b.to_dict() for n, b in self.placement.items()},
                "verify": self.report.to_dict()}


def evaluate_placements(brief: Brief, placements: list[Placement], generator: str = "", seed: int = 0) -> list[Option]:
    opts = []
    for pl in placements:
        intent = assembly_from_placement(brief, pl)
        rep = verify(brief, pl, intent)
        sc = score(rep.realised) if rep.ok and rep.realised else {}
        opts.append(Option(pl, intent.signature(), rep, sc, generator, seed))
    return opts


def rank(options: list[Option], weights: dict[str, float] | None = None) -> list[Option]:
    w = {"adjacency": 10, "deviation": -5, "compactness": 3, "circulation": -1, "stacking": 1,
         "vertical": 10, "envelope_fit": 0, "daylight": 2}
    if weights:
        w.update(weights)
    def key(o: Option) -> float:
        return sum(w[m] * o.scores.get(m, 0.0) for m in METRICS) if o.ok else -1e9
    return sorted(options, key=key, reverse=True)


def generate(gen, brief: Brief, seed: int = 0, params: dict | None = None, name: str = "") -> tuple[list[Option], float, float]:
    if not brief.expanded:  # every brief is validated; circulation sections are expanded (M7)
        from .circulation import prepare
        brief, _ = prepare(brief)  # raises BriefInvalid with plain messages
    t0 = time.perf_counter()
    placements = gen(brief, params, seed)
    t_gen = time.perf_counter() - t0
    t1 = time.perf_counter()
    options = evaluate_placements(brief, placements, name, seed)
    t_real = time.perf_counter() - t1
    return options, t_gen, t_real


def run_generator(gen, brief: Brief, seed: int = 0, params: dict | None = None, name: str = "") -> dict:
    options, t_gen, t_real = generate(gen, brief, seed, params, name)
    ok = [o for o in options if o.ok]
    distinct = len({o.signature for o in ok})
    def mean(metric: str) -> float:
        return round(sum(o.scores[metric] for o in ok) / len(ok), 4) if ok else 0.0
    return {"options": len(options), "verified": len(ok), "distinct": distinct,
            **{m: mean(m) for m in METRICS}, "t_gen": round(t_gen, 3), "t_realise": round(t_real, 3)}
