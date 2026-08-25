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
4. The Aer 0.17.2 crash workaround (`_flatten_simple_if_else_to_legacy_condition`,
   see below) silently corrupted results when the circuit ALSO contained a
   `while` loop (a WhileLoopOp): partially flattening only the teleport
   correction IfElseOps while leaving the WhileLoopOp as modern control flow
   made Aer randomize the flattened corrections instead of applying them
   correctly (mixing-all2.dqc). Fixed by skipping the entire flatten pass
   whenever the circuit contains any control-flow op the pass can't itself
   flatten (WhileLoopOp, ForLoopOp, SwitchCaseOp, or a "complex" IfElseOp),
   since Aer handles an all-modern or all-simple-flattened circuit correctly,
   but not a mix of the two.

Also guards the Aer 0.17.2 workaround (`_flatten_simple_if_else_to_legacy_condition`)
that both prevents the historical `_Map_base::at` circuit-load crash and (it
turns out) silent result corruption of the Bell-correction if_else blocks,
needed for splittable.dqc's known "No measurement counts returned" failure
mode. See /memories/repo/testing.md for the root-cause writeups.
"""
from __future__ import annotations

import multiprocessing
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

# Hard wall-clock ceiling for each Aer-executing call in this file. The Aer
# MPS backend has been observed to never return for some rule-#11-expanded
# fixtures (see /memories/repo/testing.md); running each call in a killable
# subprocess turns that indefinite hang into a bounded, reported failure
# instead of pinning a CPU core forever (the incident that forced a reboot).
_AER_CALL_TIMEOUT_S = 90


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


def _real_bit_distribution(counts: dict[str, int], correction_indices: set[int]) -> Counter:
    """Collapse a counts dict to only the "real" (non-teleport-correction)
    classical bits, keyed by their concatenated 0/1 values (throwaway
    correction bits and inter-register spaces stripped)."""
    dist: Counter = Counter()
    for reading, occurrences in counts.items():
        bits = [ch for ch in reading if ch in "01"]
        total_bits = len(bits)
        kept = [ch for pos, ch in enumerate(bits) if (total_bits - 1 - pos) not in correction_indices]
        dist["".join(kept)] += occurrences
    return dist


def _named_register_readings(counts: dict[str, int], clbit_register_names: list, register_name: str) -> Counter:
    """Collapse a counts dict down to just the bits of one named classical
    register (e.g. "ans"), keyed by that register's own bit string."""
    indices = sorted(index for index, name in enumerate(clbit_register_names) if name == register_name)
    dist: Counter = Counter()
    for reading, occurrences in counts.items():
        bits = [ch for ch in reading if ch in "01"]
        total_bits = len(bits)
        kept = "".join(bits[total_bits - 1 - i] for i in reversed(indices))
        dist[kept] += occurrences
    return dist


def _run_in_process(name: str, *, split_gen_teleports_enabled: bool, shots: int, queue) -> None:
    source = (QASM_SPLIT_ROOT / name / f"{name}.dqc").read_text(encoding="utf-8")
    split_lines = split_points_from_source(source)
    bindings = {key: "1" for key in scan_inputs(source)} or None
    result = rewrite_and_analyze(
        source,
        _rules(split_gen_teleports_enabled=split_gen_teleports_enabled),
        split_lines,
        bindings,
        shots=shots,
        timeout_s=30,
        execute_runtime=True,
    )
    # Only picklable payload crosses the process boundary (never the
    # QuantumCircuit/parse-tree themselves).
    queue.put({
        "issue_messages": [issue.message for issue in result.issues],
        "counts": dict(result.counts or {}),
        "correction_indices": teleport_correction_clbit_indices(result.circuit),
        "clbit_register_names": [
            (result.circuit.find_bit(clbit).registers[0][0].name if result.circuit.find_bit(clbit).registers else None)
            for clbit in getattr(result.circuit, "clbits", [])
        ] if result.circuit is not None else [],
    })


class _RunResult:
    def __init__(self, payload: dict) -> None:
        self.issue_messages: list[str] = payload["issue_messages"]
        self.counts: dict[str, int] = payload["counts"]
        self.correction_indices: set[int] = payload["correction_indices"]
        self.clbit_register_names: list[str | None] = payload["clbit_register_names"]


def _run(name: str, *, split_gen_teleports_enabled: bool, shots: int = 500) -> _RunResult:
    # Use "spawn", not "fork": by the time this file runs, earlier test
    # modules may have already started Qt/thread-pool background threads in
    # this same pytest process, and fork()-ing a multithreaded process risks
    # the child inheriting a locked allocator mutex and deadlocking forever
    # (see /memories/repo/testing.md). "spawn" starts a clean interpreter.
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    process = ctx.Process(target=_run_in_process, args=(name,), kwargs={"split_gen_teleports_enabled": split_gen_teleports_enabled, "shots": shots, "queue": queue})
    process.start()
    process.join(_AER_CALL_TIMEOUT_S)
    if process.is_alive():
        process.terminate()
        process.join(5)
        if process.is_alive():
            process.kill()
            process.join()
        raise AssertionError(f"{name} (rule11={split_gen_teleports_enabled}) did not complete within {_AER_CALL_TIMEOUT_S}s (Aer likely stuck)")
    if queue.empty():
        raise AssertionError(f"{name} (rule11={split_gen_teleports_enabled}) subprocess exited without a result (exit code {process.exitcode})")
    return _RunResult(queue.get())


class Rule11MeasurementConsistencyTests(unittest.TestCase):
    def _assert_matching_real_distribution(self, name: str) -> None:
        # These fixtures have a fully deterministic "real" (non-teleport-
        # correction) outcome for fixed inputs, so a handful of shots is
        # statistically sufficient; a large shot count is unnecessarily slow
        # here because each shot re-simulates the mid-circuit teleportation
        # corrections (e.g. adder+rule11 costs ~1s/shot -- 500 shots took
        # several minutes wall-clock, which looked like a hang but wasn't).
        enabled = _run(name, split_gen_teleports_enabled=True, shots=5)
        disabled = _run(name, split_gen_teleports_enabled=False, shots=5)
        self.assertFalse(enabled.issue_messages, f"{name} (rule 11 on) issues: {enabled.issue_messages}")
        self.assertFalse(disabled.issue_messages, f"{name} (rule 11 off) issues: {disabled.issue_messages}")
        self.assertTrue(enabled.counts, f"{name} (rule 11 on) returned no measurement counts")
        self.assertTrue(disabled.counts, f"{name} (rule 11 off) returned no measurement counts")

        enabled_dist = _real_bit_distribution(enabled.counts, enabled.correction_indices)
        disabled_dist = _real_bit_distribution(disabled.counts, disabled.correction_indices)
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
            self.assertFalse(result.issue_messages, result.issue_messages)
            dist = _real_bit_distribution(result.counts, result.correction_indices)
            self.assertLessEqual(set(dist), {"00", "11"}, f"bell_state (rule 11 {enabled}): unexpected uncorrelated readings {dist}")

    def test_splittable_runs_on_aer_across_rule_11_toggle(self) -> None:
        # Regression for the Aer 0.17.2 "_Map_base::at" / "No measurement
        # counts returned" failure mode on this exact fixture.
        for enabled in (True, False):
            result = _run("splittable", split_gen_teleports_enabled=enabled, shots=500)
            self.assertFalse(result.issue_messages, result.issue_messages)
            self.assertTrue(result.counts, f"splittable (rule 11 {enabled}) returned no measurement counts")

    def test_mixing_all2_matches_across_rule_11_toggle(self) -> None:
        # Regression for a `while` loop elsewhere in the circuit silently
        # corrupting rule #11's flattened teleport corrections (see bug 4
        # above). Only the ripple-carry adder's "ans" register is checked
        # here (not the whole circuit): mixing-all2.dqc also contains a
        # genuinely random `while` loop and Hadamard-based measurements
        # (c_b0-c_b3) elsewhere, so a full-distribution comparison would
        # fail regardless of rule #11. With a_in=1, b_in=3 fixed in the
        # source, "ans" (bb + cout, the adder's sum) must always read "100".
        for enabled in (True, False):
            result = _run("mixing-all2", split_gen_teleports_enabled=enabled, shots=300)
            self.assertFalse(result.issue_messages, result.issue_messages)
            self.assertTrue(result.counts, f"mixing-all2 (rule 11 {enabled}) returned no measurement counts")
            ans_dist = _named_register_readings(result.counts, result.clbit_register_names, "ans")
            self.assertEqual(set(ans_dist), {"100"}, f"mixing-all2 (rule 11 {enabled}): unexpected 'ans' readings {ans_dist}")


if __name__ == "__main__":
    unittest.main()
