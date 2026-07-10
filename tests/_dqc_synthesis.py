from __future__ import annotations

import random
from pathlib import Path

from app.pipeline import build_distributed_qasm, line_is_inside_blocking_scope


def _guarded_split_candidates(source: str) -> list[int]:
    candidates: list[int] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if not stripped.endswith(";"):
            continue
        if stripped.startswith(("OPENQASM", "include", "qubit", "bit", "input", "const")):
            continue
        if line_is_inside_blocking_scope(source, line_no):
            continue
        candidates.append(line_no)
    return candidates


def choose_guarded_split_points(source: str, desired_points: int = 2, seed: int = 7) -> set[int]:
    candidates = _guarded_split_candidates(source)
    if not candidates or desired_points <= 0:
        return set()
    rng = random.Random(seed)
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    selected = sorted(shuffled[: min(desired_points, len(shuffled))])
    return set(selected)


def synthesize_dqc_source_from_qasm(source: str, desired_points: int = 2, seed: int = 7) -> tuple[str, set[int]]:
    split_points = choose_guarded_split_points(source, desired_points=desired_points, seed=seed)
    dqc_source, _ = build_distributed_qasm(source, split_points)
    return dqc_source, split_points


def synthesize_dqc_file_from_qasm(qasm_path: Path, output_dir: Path, desired_points: int = 2, seed: int = 7) -> tuple[Path, set[int]]:
    source = qasm_path.read_text(encoding="utf-8")
    dqc_source, split_points = synthesize_dqc_source_from_qasm(source, desired_points=desired_points, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{qasm_path.stem}.dqc"
    target.write_text(dqc_source, encoding="utf-8")
    return target, split_points