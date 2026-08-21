"""
Regression guard: toggling rule #11 (split-generated teleportations) must not
change the *measured outcomes* of a circuit's "real" (non-instrumental)
classical bits, only add/remove the throw-away teleportation correction bits.

This covers three separate bugs found and fixed together (2026-08-21):
1. `QuantumBarrier` statements were treated as a data dependency by
   compute_chunk_flows, spuriously pulling a qubit into (and destructively
   measuring it for) a chunk that never actually used it, corrupting a later
   chunk that legitimately needed the same original qubit (rb.dqc).
2. Loop-unrolling (rule #7) left constant index arithmetic unresolved (e.g.
   `b[i + 1]` with `i` substituted to `2` became the literal text `b[2 + 1]`
   instead of `b[3]`), so later teleport-alias renaming (which matches by
   literal operand text) silently missed it and kept referencing the stale,
   already-measured original qubit (adder.dqc).
3. `resolve_split_anchors` counted a split anchor's position including any
   literal `pragma dqc.v1.split id=N` lines still present in the stream, but
   `add_split_markers` re-inserts markers against the pragma-*stripped* line
   numbering -- any split boundary preceded by another split's own literal
   pragma line drifted by one line per preceding pragma, splitting a
   broadcast-unfolded statement (e.g. `c = measure q;` -> two lines) in the
   wrong place (bell_state.dqc, and any multi-split circuit combined with
   rules #1+#2 dropping comments/blanks alongside #10's broadcast unfolding).

Also guards the Aer 0.17.2 workaround (`_flatten_simple_if_else_to_legacy_condition`)
that both prevents the historical `_Map_base::at` circuit-load crash and (it
turns out) silent result corruption of the Bell-correction if_else blocks,
needed for splittable.dqc's known "No measurement counts returned" failure
mode. See /memories/repo/testing.md for the root-cause writeups.
"""
from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from app.pipeline import (
    DEFAULT_RULES,
    RULE_ID_SPLIT_GEN_TELEPORTS,
    RuleState,
    rewrite_and_analyze,
    scan_inputs,
    split_points_from_source,
    teleport_correction_clbit_indices,
)

QASM_SPLIT_ROOT = Path(__file__).resolve().parents[1] / "qasm" / "split"


def _rules(*, split_gen_teleports_enabled: bool) -> list[RuleState]:
    return [
        RuleState(
            rule.rule_id,
            rule.name,
            rule.description,
            rule.rule_id != 0 and (rule.rule_id != RULE_ID_SPLIT_GEN_TELEPORTS or split_gen_teleports_enabled),
        )
        for rule in DEFAULT_RULES
    ]


def _real_bit_distribution(counts: dict[str, int], circuit) -> Counter:
    """Collapse a counts dict to only the "real" (non-teleport-correction)
    classical bits, keyed by their concatenated 0/1 values (throwaway
    correction bits and inter-register spaces stripped)."""
    correction_indices = teleport_correction_clbit_indices(circuit)
    dist: Counter = Counter()
    for reading, occurrences in counts.items():
        bits = [ch for ch in reading if ch in "01"]
        total_bits = len(bits)
        kept = [ch for pos, ch in enumerate(bits) if (total_bits - 1 - pos) not in correction_indices]
        dist["".join(kept)] += occurrences
    return dist


def _run(name: str, *, split_gen_teleports_enabled: bool, shots: int = 500):
    source = (QASM_SPLIT_ROOT / name / f"{name}.dqc").read_text(encoding="utf-8")
    split_lines = split_points_from_source(source)
    bindings = {key: "1" for key in scan_inputs(source)} or None
    return rewrite_and_analyze(
        source,
        _rules(split_gen_teleports_enabled=split_gen_teleports_enabled),
        split_lines,
        bindings,
        shots=shots,
        timeout_s=30,
        execute_runtime=True,
    )


class Rule11MeasurementConsistencyTests(unittest.TestCase):
    def _assert_matching_real_distribution(self, name: str) -> None:
        enabled = _run(name, split_gen_teleports_enabled=True)
        disabled = _run(name, split_gen_teleports_enabled=False)
        self.assertFalse(enabled.issues, f"{name} (rule 11 on) issues: {[i.message for i in enabled.issues]}")
        self.assertFalse(disabled.issues, f"{name} (rule 11 off) issues: {[i.message for i in disabled.issues]}")
        self.assertTrue(enabled.counts, f"{name} (rule 11 on) returned no measurement counts")
        self.assertTrue(disabled.counts, f"{name} (rule 11 off) returned no measurement counts")

        enabled_dist = _real_bit_distribution(enabled.counts, enabled.circuit)
        disabled_dist = _real_bit_distribution(disabled.counts, disabled.circuit)
        self.assertEqual(
            dict(enabled_dist),
            dict(disabled_dist),
            f"{name}: real-bit measurement distribution changed when toggling rule #11",
        )

    def test_adder_matches_across_rule_11_toggle(self) -> None:
        self._assert_matching_real_distribution("adder")

    def test_rb_matches_across_rule_11_toggle(self) -> None:
        self._assert_matching_real_distribution("rb")

    def test_bernstein_vazirani_matches_across_rule_11_toggle(self) -> None:
        self._assert_matching_real_distribution("bernstein-vazirani")

    def test_qiskit_example_matches_across_rule_11_toggle(self) -> None:
        self._assert_matching_real_distribution("qiskit-example")

    def test_bell_state_stays_perfectly_correlated_across_rule_11_toggle(self) -> None:
        # bell_state.dqc's outcome is genuinely random (Hadamard), but |00> and
        # |11> must be the *only* possible readings regardless of rule #11.
        for enabled in (True, False):
            result = _run("bell_state", split_gen_teleports_enabled=enabled, shots=500)
            self.assertFalse(result.issues, [i.message for i in result.issues])
            dist = _real_bit_distribution(result.counts, result.circuit)
            self.assertLessEqual(set(dist), {"00", "11"}, f"bell_state (rule 11 {enabled}): unexpected uncorrelated readings {dist}")

    def test_splittable_runs_on_aer_across_rule_11_toggle(self) -> None:
        # Regression for the Aer 0.17.2 "_Map_base::at" / "No measurement
        # counts returned" failure mode on this exact fixture.
        for enabled in (True, False):
            result = _run("splittable", split_gen_teleports_enabled=enabled, shots=500)
            self.assertFalse(result.issues, [i.message for i in result.issues])
            self.assertTrue(result.counts, f"splittable (rule 11 {enabled}) returned no measurement counts")


if __name__ == "__main__":
    unittest.main()
