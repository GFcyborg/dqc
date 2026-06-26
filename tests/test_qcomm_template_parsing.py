"""Unit tests for the q-comm_template.qasm parsing and validation logic.

The adaptation pipeline in pipeline.py reads ``q-comm_template.qasm`` and
renames a fixed set of placeholder identifiers for each split-point dependency.
These tests verify:

  1.  ``validate_qcomm_template`` accepts the on-disk template without errors.
  2.  ``validate_qcomm_template`` catches every missing required pattern.
  3.  ``_suffix_template_symbol_names`` renames identifiers correctly.
  4.  ``_adapt_template_for_dependency`` removes the q_SOURCE declaration and
      substitutes the actual qubit name.
  5.  The mangling rules are correct for scalar and array qubit names.
  6.  The template can be adapted for multiple split IDs without name collisions.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from app.pipeline import (
    QCOMM_TEMPLATE_REQUIRED_IDENTIFIERS,
    QCOMM_TEMPLATE_SOURCE_DECL_RE,
    _adapt_template_for_dependency,
    _suffix_template_symbol_names,
    validate_qcomm_template,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEMPLATE_PATH = Path(__file__).parent.parent / "app" / "q-comm_template.qasm"


def _load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _template_lines() -> list[str]:
    return _load_template().replace("\r\n", "\n").replace("\r", "\n").splitlines()


# ---------------------------------------------------------------------------
# 1. On-disk template must be valid
# ---------------------------------------------------------------------------

class TestOnDiskTemplate(unittest.TestCase):
    def test_template_file_exists(self) -> None:
        self.assertTrue(TEMPLATE_PATH.exists(), f"Template not found: {TEMPLATE_PATH}")

    def test_template_validates_cleanly(self) -> None:
        errors = validate_qcomm_template(_load_template())
        self.assertEqual(
            errors,
            [],
            "On-disk template has validation errors:\n  " + "\n  ".join(errors),
        )

    def test_template_contains_source_decl_line(self) -> None:
        text = _load_template()
        self.assertIsNotNone(
            QCOMM_TEMPLATE_SOURCE_DECL_RE.search(text),
            "Template must contain the line 'qubit q_SOURCE;'",
        )

    def test_template_contains_all_required_identifiers(self) -> None:
        text = _load_template()
        for ident in QCOMM_TEMPLATE_REQUIRED_IDENTIFIERS:
            pattern = re.compile(rf"\b{re.escape(ident)}\b")
            self.assertIsNotNone(
                pattern.search(text),
                f"Required identifier '{ident}' not found in template",
            )


# ---------------------------------------------------------------------------
# 2. validate_qcomm_template detects missing patterns
# ---------------------------------------------------------------------------

class TestValidateQcommTemplate(unittest.TestCase):
    def test_valid_template_returns_empty_list(self) -> None:
        self.assertEqual(validate_qcomm_template(_load_template()), [])

    def test_missing_source_decl_is_reported(self) -> None:
        # Remove the declaration line.
        text = "\n".join(
            line for line in _load_template().splitlines()
            if not QCOMM_TEMPLATE_SOURCE_DECL_RE.match(line)
        )
        errors = validate_qcomm_template(text)
        self.assertTrue(
            any("q_SOURCE" in e and "declaration" in e.lower() for e in errors),
            f"Expected a source-decl error, got: {errors}",
        )

    def test_missing_q_epr_target_is_reported(self) -> None:
        text = _load_template().replace("q_epr_TARGET", "q_epr_DEST")
        errors = validate_qcomm_template(text)
        self.assertTrue(
            any("q_epr_TARGET" in e for e in errors),
            f"Expected q_epr_TARGET error, got: {errors}",
        )

    def test_missing_q_epr_is_reported(self) -> None:
        # Replace q_epr (but not q_epr_TARGET) so only q_epr is missing.
        text = re.sub(r"\bq_epr\b", "q_entangle", _load_template())
        errors = validate_qcomm_template(text)
        self.assertTrue(
            any("q_epr" in e and "q_epr_TARGET" not in e for e in errors),
            f"Expected q_epr error, got: {errors}",
        )

    def test_missing_zcorrect_is_reported(self) -> None:
        text = _load_template().replace("telept_Zcorrect_q", "telept_ZZ_q")
        errors = validate_qcomm_template(text)
        self.assertTrue(
            any("telept_Zcorrect_q" in e for e in errors),
            f"Expected telept_Zcorrect_q error, got: {errors}",
        )

    def test_missing_xcorrect_is_reported(self) -> None:
        text = _load_template().replace("telept_Xcorrect_q", "telept_XX_q")
        errors = validate_qcomm_template(text)
        self.assertTrue(
            any("telept_Xcorrect_q" in e for e in errors),
            f"Expected telept_Xcorrect_q error, got: {errors}",
        )

    def test_empty_template_reports_all_required(self) -> None:
        errors = validate_qcomm_template("")
        # Every required identifier plus the source-decl must be reported.
        self.assertGreaterEqual(len(errors), len(QCOMM_TEMPLATE_REQUIRED_IDENTIFIERS))


# ---------------------------------------------------------------------------
# 3. _suffix_template_symbol_names renaming
# ---------------------------------------------------------------------------

class TestSuffixTemplateSymbolNames(unittest.TestCase):
    def _adapt(self, source_qubit: str, split_id: int) -> list[str]:
        return _suffix_template_symbol_names(_template_lines(), split_id, source_qubit)

    def test_q_epr_target_renamed(self) -> None:
        adapted = self._adapt("w", 3)
        joined = "\n".join(adapted)
        self.assertIn("w_epr_TARGET_3", joined)
        # Original token must be gone
        self.assertNotIn("q_epr_TARGET", joined)

    def test_q_epr_renamed(self) -> None:
        adapted = self._adapt("w", 3)
        joined = "\n".join(adapted)
        self.assertIn("w_epr_3", joined)

    def test_zcorrect_renamed(self) -> None:
        adapted = self._adapt("w", 3)
        joined = "\n".join(adapted)
        self.assertIn("telept_Zcorrect_w_3", joined)

    def test_xcorrect_renamed(self) -> None:
        adapted = self._adapt("w", 3)
        joined = "\n".join(adapted)
        self.assertIn("telept_Xcorrect_w_3", joined)

    def test_q_source_not_renamed_by_suffix(self) -> None:
        # _suffix_template_symbol_names must NOT touch q_SOURCE (that's done
        # in _adapt_template_for_dependency instead).
        adapted = self._adapt("w", 3)
        joined = "\n".join(adapted)
        self.assertIn("q_SOURCE", joined)

    def test_different_split_ids_produce_different_names(self) -> None:
        a = "\n".join(self._adapt("q", 1))
        b = "\n".join(self._adapt("q", 2))
        self.assertIn("q_epr_1", a)
        self.assertIn("q_epr_2", b)
        self.assertNotIn("q_epr_2", a)
        self.assertNotIn("q_epr_1", b)


# ---------------------------------------------------------------------------
# 4. _adapt_template_for_dependency – full adaptation
# ---------------------------------------------------------------------------

class TestAdaptTemplateForDependency(unittest.TestCase):
    def _adapt(self, source_qubit: str, split_id: int) -> list[str]:
        return _adapt_template_for_dependency(_template_lines(), split_id, source_qubit)

    def test_source_decl_line_removed(self) -> None:
        adapted = self._adapt("myq", 1)
        for line in adapted:
            self.assertFalse(
                QCOMM_TEMPLATE_SOURCE_DECL_RE.match(line),
                f"Source declaration line must be removed, but found: {line!r}",
            )

    def test_q_source_placeholder_replaced(self) -> None:
        adapted = self._adapt("myq", 1)
        joined = "\n".join(adapted)
        self.assertNotIn("q_SOURCE", joined, "q_SOURCE placeholder must be replaced")
        self.assertIn("myq", joined)

    def test_scalar_qubit_name_used_verbatim(self) -> None:
        adapted = self._adapt("anc", 2)
        joined = "\n".join(adapted)
        # EPR and classical bits derive from the source name
        self.assertIn("anc_epr_2", joined)
        self.assertIn("anc_epr_TARGET_2", joined)
        self.assertIn("telept_Zcorrect_anc_2", joined)
        self.assertIn("telept_Xcorrect_anc_2", joined)

    def test_array_element_brackets_stripped_in_names(self) -> None:
        # The pipeline strips brackets from array names before calling this
        # function, so we test the bracket-free form that actually arrives.
        adapted = self._adapt("q0", 5)
        joined = "\n".join(adapted)
        self.assertIn("q0_epr_5", joined)
        self.assertIn("telept_Zcorrect_q0_5", joined)

    def test_output_is_non_empty_valid_qasm_lines(self) -> None:
        adapted = self._adapt("q", 1)
        self.assertGreater(len(adapted), 0)
        # Every non-comment, non-blank line should end with ';' or ')' or '}'
        # (basic QASM statement terminator check)
        for line in adapted:
            stripped = line.strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("/*") and not stripped.startswith("*"):
                self.assertTrue(
                    stripped.endswith(";") or stripped.endswith(")") or stripped.endswith("}"),
                    f"Unexpected line ending: {line!r}",
                )

    def test_multiple_split_points_no_name_collision(self) -> None:
        a = set(_adapt_template_for_dependency(_template_lines(), 1, "q"))
        b = set(_adapt_template_for_dependency(_template_lines(), 2, "q"))
        # The adapted lines for different split IDs must be disjoint (different names)
        # except for lines that do not contain any mangled identifier.
        mangled_a = {ln for ln in a if "_1" in ln}
        mangled_b = {ln for ln in b if "_2" in ln}
        self.assertEqual(mangled_a & mangled_b, set())


# ---------------------------------------------------------------------------
# 5. QCOMM_TEMPLATE_SOURCE_DECL_RE correctness
# ---------------------------------------------------------------------------

class TestSourceDeclRegex(unittest.TestCase):
    def test_matches_exact_decl(self) -> None:
        self.assertIsNotNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("qubit q_SOURCE;"))

    def test_matches_with_leading_whitespace(self) -> None:
        self.assertIsNotNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("  qubit q_SOURCE;"))

    def test_matches_with_trailing_whitespace(self) -> None:
        self.assertIsNotNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("qubit q_SOURCE;   "))

    def test_does_not_match_array_decl(self) -> None:
        self.assertIsNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("qubit[1] q_SOURCE;"))

    def test_does_not_match_partial_name(self) -> None:
        self.assertIsNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("qubit q_SOURCE_extra;"))

    def test_does_not_match_comment(self) -> None:
        self.assertIsNone(QCOMM_TEMPLATE_SOURCE_DECL_RE.search("// qubit q_SOURCE;"))


if __name__ == "__main__":
    unittest.main()
