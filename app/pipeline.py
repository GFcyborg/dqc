from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError
from urllib.request import urlopen
import importlib.metadata
import json
import math
import re
import time

import networkx as nx

try:
    import kahypar as _kahypar  # type: ignore
except Exception:
    _kahypar = None


STDGATE_NAMES = {
    "barrier",
    "ccx",
    "cphase",
    "cswap",
    "cx",
    "cy",
    "cz",
    "gphase",
    "h",
    "id",
    "iswap",
    "measure",
    "p",
    "reset",
    "rx",
    "ry",
    "rz",
    "s",
    "sdg",
    "swap",
    "sx",
    "sxdg",
    "t",
    "tdg",
    "u",
    "u1",
    "u2",
    "u3",
    "x",
    "y",
    "z",
}

INPUT_PATTERN = re.compile(r"^\s*input\s+[^;]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$", re.MULTILINE)
GATE_DEF_PATTERN = re.compile(r"^\s*gate\s+([A-Za-z_][A-Za-z0-9_]*)\b")
DECL_PATTERN = re.compile(r"^\s*(?:qubit(?:\[[^\]]+\])?|bit(?:\[[^\]]+\])?|int(?:\[[^\]]+\])?|uint(?:\[[^\]]+\])?|float(?:\[[^\]]+\])?|bool|array\b|const\b|input\b|let\b)\s+([A-Za-z_][A-Za-z0-9_]*)")
IDENT_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
# Match end-of-line comments (// up to newline) or block comments (/* ... */ non-greedy)
COMMENT_PATTERN = re.compile(r"//[^\n\r]*|/\*.*?\*/", re.DOTALL)
HEADER_PATTERN = re.compile(r"^\s*OPENQASM\s+3(?:\.\d+)?\s*;", re.IGNORECASE)
INCLUDE_PATTERN = re.compile(r"^\s*include\s+\"stdgates\.inc\"\s*;", re.IGNORECASE)
DQC_PRAGMA_PATTERN = re.compile(r"^\s*pragma\s+dqc\.v1\.split\s+id\s*=\s*(?P<id>[1-9][0-9]*)\s*$", re.IGNORECASE)
BIT_DECL_PATTERN = re.compile(r"^\s*bit(?:\[[^\]]+\])?\s+([A-Za-z_][A-Za-z0-9_]*)\s*;\s*(?://.*)?$", re.MULTILINE)
BIT_IF_CAST_PATTERN = re.compile(r"^(?P<prefix>\s*if\s*\(\s*)(?P<expr>[A-Za-z_][A-Za-z0-9_]*(?:\s*\[[^\]]+\])*)\s*==\s*(?P<value>[01])\s*(?P<suffix>\)\s*.*)$")
UINT_TOKEN_PATTERN = re.compile(r"\buint\b")
UINT_DECL_PATTERN = re.compile(r"^(?P<indent>\s*)uint\[(?P<width>\d+)\]\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(?P<value>[^;]+))?\s*;\s*(?://.*)?$")
FOR_UINT_RANGE_PATTERN = re.compile(r"^(?P<indent>\s*)for\s+uint\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+in\s*\[(?P<range>[^\]]+)\]\s*\{\s*(?P<body>.*)\s*\}\s*(?://.*)?$")
FOR_UINT_START_PATTERN = re.compile(r"^(?P<indent>\s*)for\s+uint\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+in\s*\[(?P<range>[^\]]+)\]\s*\{\s*(?://.*)?$")
IF_CONST_BOOL_PATTERN = re.compile(r"^(?P<indent>\s*)if\s*\(\s*(?P<bool>true|false)\s*\)\s*(?P<tail>.*)$", re.IGNORECASE)
SCALAR_QUBIT_DECL_PATTERN = re.compile(r"^(?P<indent>\s*)qubit\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*;(?P<suffix>\s*(?://.*)?)$")
SCALAR_BIT_DECL_PATTERN = re.compile(r"^(?P<indent>\s*)bit\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*;(?P<suffix>\s*(?://.*)?)$")
IF_SCALAR_BIT_COND_PATTERN = re.compile(r"^(?P<prefix>\s*if\s*\(\s*)(?P<expr>!?\s*[A-Za-z_][A-Za-z0-9_]*)(?P<suffix>\s*\)\s*.*)$")
AUTO_PARAM_DEFAULT_EXPR = "pi/2 - 1"
AUTO_PARAM_DEFAULT_VALUE = (math.pi / 2.0) - 1.0
OPENQASM_3_1_HEADER_RE = re.compile(r"(?im)^\s*OPENQASM\s+3\.1\b")
STDGATES_INCLUDE_RE = re.compile(r'(?im)^\s*include\s+"stdgates\.inc"\s*;\s*$')


@dataclass(slots=True)
class RewriteSpan:
    line: int
    original: str
    rewritten: str
    rule_id: int
    message: str
    kind: str = "info"


@dataclass(slots=True)
class RewriteResult:
    source: str
    rewritten_source: str
    spans: list[RewriteSpan] = field(default_factory=list)
    issues: list[RewriteSpan] = field(default_factory=list)
    parse_tree: Any | None = None
    circuit: Any | None = None
    counts: dict[str, int] = field(default_factory=dict)
    duration_s: float = 0.0
    started_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    split_source: str = ""
    split_qasm: str = ""
    chunk_flows: list[Any] = field(default_factory=list)
    chunk_graph: nx.DiGraph | None = None
    interaction_graph: nx.Graph | None = None
    dag_graph: nx.DiGraph | None = None
    ast_graph: nx.DiGraph | None = None
    suggested_split_points: list[int] = field(default_factory=list)
    suggestion_reason: str = ""


@dataclass(slots=True)
class RuleState:
    rule_id: int
    name: str
    description: str
    enabled: bool = True


@dataclass(slots=True)
class ChunkFlow:
    title: str
    original_text: str
    rewritten_text: str
    defined: set[str]
    used: set[str]
    incoming_sources: dict[str, set[int]]
    outgoing_targets: dict[str, set[int]]


DEFAULT_RULES = [
    RuleState(0, "Bypass all rewrites", "Temporarily ignore all the other rules without losing their toggle states."),
    RuleState(1, "Drop comments", "Remove single-line comments from the transpiled output."),
    RuleState(2, "Drop blank lines", "Compact the transpiled output by removing empty lines."),
    RuleState(3, "Inject OPENQASM 3.1", "Insert a version header when the source does not declare one."),
    RuleState(4, "Inject stdgates", "Insert include \"stdgates.inc\" when it is missing."),
    RuleState(5, "Rename colliding gates", "Prefix custom gate definitions that collide with stdgates.inc."),
    RuleState(6, "Split-generated teleportations", "Rewrite split pragmas into folded teleportation comment blocks in the rewritten view."),
    RuleState(7, "Bit-to-bool Cast", "Rewrite `if(bit == 1)` to `if(bit)` and `if(bit == 0)` to `if(!bit)`."),
    RuleState(8, "Uint Workaround", "Lower uint declarations/usages into importer-safe forms (const folding, loop unrolling, and guard simplification)."),
]

INNER_SCOPE_BLOCKING_KINDS = {
    "QuantumGateDefinition",
    "ForInLoop",
    "WhileLoop",
    "BranchingStatement",
    "Box",
    "SubroutineDefinition",
    "CalibrationDefinition",
    "CalibrationGrammarDeclaration",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _iter_ast_nodes(node: Any) -> Iterable[Any]:
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_ast_nodes(value)
        return
    if isinstance(node, (list, tuple, set)):
        for value in node:
            yield from _iter_ast_nodes(value)
        return
    fields = getattr(node, "__dict__", {})
    for key, value in fields.items():
        if key.startswith("_") or key == "span":
            continue
        yield from _iter_ast_nodes(value)


def line_is_inside_blocking_scope(source: str, line: int) -> bool:
    if line < 1:
        return False
    try:
        program = safe_import_qasm3()(source)
    except Exception:
        return False
    for node in _iter_ast_nodes(program):
        if type(node).__name__ not in INNER_SCOPE_BLOCKING_KINDS:
            continue
        s = getattr(node, "span", None) or getattr(node, "_span", None)
        if s is None:
            continue
        start = int(getattr(s, "start_line", 0) or 0)
        end = int(getattr(s, "end_line", 0) or 0)
        if start <= line < end:
            return True
    return False


def scan_inputs(source: str) -> list[str]:
    return INPUT_PATTERN.findall(source)


def substitute_inputs(source: str, values: dict[str, str]) -> str:
    lines: list[str] = []
    for line in source.splitlines():
        match = INPUT_PATTERN.match(line)
        if not match:
            lines.append(line)
            continue
        name = match.group(1)
        if name in values:
            replacement = re.sub(r"^\s*input\s+", "const ", line)
            replacement = replacement[:-1] + f" = {values[name]};"
            lines.append(replacement)
        else:
            lines.append(re.sub(r"^\s*input\s+", "const ", line[:-1]) + f" = {AUTO_PARAM_DEFAULT_EXPR};")
    return "\n".join(lines)


def _bind_circuit_parameters(circuit: Any, parameter_bindings: dict[str, str] | None) -> Any:
    if not getattr(circuit, "num_parameters", 0):
        return circuit

    def _eval_parameter_text(value_text: str) -> Any | None:
        expr = value_text.strip()
        if not expr:
            return None
        expr = expr.replace("π", "pi")
        expr = re.sub(r"\btrue\b", "True", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bfalse\b", "False", expr, flags=re.IGNORECASE)
        expr = expr.replace("&&", " and ").replace("||", " or ")
        expr = re.sub(r"!\s*(?!=)", " not ", expr)
        expr = re.sub(r"\bpi\b", "math.pi", expr)
        expr = re.sub(r"\btau\b", "math.tau", expr)
        expr = re.sub(r"\beuler_gamma\b", "math.euler_gamma", expr)
        try:
            import math

            return eval(expr, {"__builtins__": {}, "math": math, "bool": bool, "int": int, "float": float}, {})
        except Exception:
            return None

    resolved_bindings = parameter_bindings or {}
    bindings: dict[Any, Any] = {}
    for parameter in getattr(circuit, "parameters", []):
        value_text = resolved_bindings.get(getattr(parameter, "name", ""), "")
        value = _eval_parameter_text(value_text) if value_text else None
        if value is None:
            value = AUTO_PARAM_DEFAULT_VALUE
        bindings[parameter] = value
    if not bindings:
        return circuit
    return circuit.assign_parameters(bindings)


def normalize_lines(source: str) -> list[str]:
    return source.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _strip_comments_preserve_columns(line: str, in_block_comment: bool) -> tuple[str, bool, list[tuple[int, int]]]:
    """Return a line with comment characters replaced by spaces.

    The output keeps column positions stable so regex match spans still map back
    to the original text for highlighting/tooltips.
    """
    out: list[str] = []
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(line)
    while i < n:
        if in_block_comment:
            end = line.find("*/", i)
            if end == -1:
                spans.append((i, n))
                out.append(" " * (n - i))
                return "".join(out), True, spans
            span_end = end + 2
            spans.append((i, span_end))
            out.append(" " * (span_end - i))
            i = span_end
            in_block_comment = False
            continue

        if line.startswith("//", i):
            spans.append((i, n))
            out.append(" " * (n - i))
            break

        if line.startswith("/*", i):
            in_block_comment = True
            continue

        out.append(line[i])
        i += 1

    return "".join(out), in_block_comment, spans


def _comment_aware_code_and_spans(lines: list[str]) -> tuple[list[str], dict[int, list[tuple[int, int]]]]:
    code_lines: list[str] = []
    comment_spans: dict[int, list[tuple[int, int]]] = {}
    in_block = False
    for line_no, line in enumerate(lines, start=1):
        code_line, in_block, spans = _strip_comments_preserve_columns(line, in_block)
        code_lines.append(code_line)
        if spans:
            comment_spans[line_no] = spans
    return code_lines, comment_spans


def maybe_add_header(lines: list[str], enabled: bool, spans: list[RewriteSpan]) -> list[str]:
    if not enabled or any(HEADER_PATTERN.match(line) for line in lines):
        return lines
    spans.append(RewriteSpan(1, "", "OPENQASM 3.1;", 3, "Inserted missing OPENQASM header."))
    return ["OPENQASM 3.1;"] + lines


def maybe_add_include(lines: list[str], enabled: bool, spans: list[RewriteSpan]) -> list[str]:
    if not enabled or any(INCLUDE_PATTERN.match(line) for line in lines):
        return lines
    insert_at = 1 if lines and HEADER_PATTERN.match(lines[0]) else 0
    spans.append(RewriteSpan(insert_at + 1, "", 'include "stdgates.inc";', 4, "Inserted stdgates include."))
    return lines[:insert_at] + ['include "stdgates.inc";'] + lines[insert_at:]


def rewrite_comments_and_blanks_with_map(lines: list[str], drop_comments: bool, drop_blanks: bool, spans: list[RewriteSpan], original_lines: list[str] | None = None) -> tuple[list[str], list[int]]:
    """Drop comments only from lines that exist in original_lines (if provided), otherwise from all lines."""
    rewritten: list[str] = []
    kept_line_numbers: list[int] = []
    
    # Step 1: Drop comments (only original ones if original_lines provided)
    if drop_comments:
        source_ref = original_lines if original_lines else lines
        _, source_comment_spans = _comment_aware_code_and_spans(source_ref)

        for line_no, line in enumerate(source_ref, start=1):
            for start, end in source_comment_spans.get(line_no, []):
                comment = line[start:end]
                if comment.strip():
                    spans.append(RewriteSpan(line_no, comment, "", 1, "Removed comment."))

        if source_comment_spans:
            processed_lines: list[str] = []
            for line_no, line in enumerate(lines, start=1):
                spans_for_line = source_comment_spans.get(line_no, [])
                if not spans_for_line:
                    processed_lines.append(line)
                    continue
                rebuilt = line
                for start, end in sorted(spans_for_line, reverse=True):
                    rebuilt = rebuilt[:start] + rebuilt[end:]
                processed_lines.append(rebuilt)
            lines = processed_lines
        
    # Step 2: Drop blank lines
    for line_no, line in enumerate(lines, start=1):
        candidate = line.rstrip()
        if not candidate.strip():
            if drop_blanks:
                spans.append(RewriteSpan(line_no, line, "", 2, "Removed blank line."))
                continue
            rewritten.append("")
            kept_line_numbers.append(line_no)
            continue
        rewritten.append(candidate)
        kept_line_numbers.append(line_no)

    return rewritten, kept_line_numbers


def rewrite_comments_and_blanks(lines: list[str], drop_comments: bool, drop_blanks: bool, spans: list[RewriteSpan], original_lines: list[str] | None = None) -> list[str]:
    rewritten, _ = rewrite_comments_and_blanks_with_map(lines, drop_comments, drop_blanks, spans, original_lines=original_lines)
    return rewritten


def remap_split_points(split_points: set[int], kept_line_numbers: list[int]) -> set[int]:
    if not split_points:
        return set()
    remapped: set[int] = set()
    for split_point in split_points:
        for new_line_no, original_line_no in enumerate(kept_line_numbers, start=1):
            if original_line_no >= split_point:
                remapped.add(new_line_no)
                break
        else:
            remapped.add(len(kept_line_numbers) + 1)
    return remapped


def shift_split_points(split_points: set[int], insert_at: int, count: int = 1) -> set[int]:
    if not split_points or count <= 0:
        return set(split_points)
    return {point + count if point >= insert_at else point for point in split_points}


def rename_colliding_gates(lines: list[str], enabled: bool, spans: list[RewriteSpan]) -> list[str]:
    if not enabled:
        return lines
    # First pass: detect all custom gate definitions that collide with stdgates.
    renamed: dict[str, str] = {}
    for line in lines:
        match = GATE_DEF_PATTERN.match(line)
        if not match:
            continue
        gate_name = match.group(1)
        if gate_name in STDGATE_NAMES and gate_name not in renamed:
            renamed[gate_name] = f"my_{gate_name}"

    if not renamed:
        return lines

    out: list[str] = []
    for line_no, line in enumerate(lines, start=1):
        rewritten = line
        for old_name, new_name in renamed.items():
            rewritten = re.sub(rf"\b{re.escape(old_name)}\b", new_name, rewritten)
        if rewritten != line:
            gate_match = GATE_DEF_PATTERN.match(line)
            if gate_match and gate_match.group(1) in renamed:
                old_name = gate_match.group(1)
                spans.append(RewriteSpan(line_no, line, rewritten, 5, f"Renamed colliding gate '{old_name}' to '{renamed[old_name]}'."))
            else:
                spans.append(RewriteSpan(line_no, line, rewritten, 5, "Updated colliding gate reference to use the my_ prefix."))
        out.append(rewritten)
    return out


def normalize_scalar_register_declarations(source: str) -> str:
    """Preserve names of standalone qubit/bit registers for qiskit wire labels.

    qiskit_qasm3_import can parse `qubit anc;` into an anonymous wire (uid-only),
    which then shows as numeric/uid labels in circuit and DAG views. Converting
    to `qubit[1] anc;` keeps the user-facing wire name.

    The same normalization for `bit c;` -> `bit[1] c;` keeps classical wire labels
    stable across circuit and graph views.
    """

    normalized_lines: list[str] = []
    scalar_bit_names: set[str] = set()
    for line in source.splitlines():
        qubit_match = SCALAR_QUBIT_DECL_PATTERN.match(line)
        if qubit_match:
            indent = qubit_match.group("indent")
            name = qubit_match.group("name")
            suffix = qubit_match.group("suffix") or ""
            normalized_lines.append(f"{indent}qubit[1] {name};{suffix}")
            continue

        bit_match = SCALAR_BIT_DECL_PATTERN.match(line)
        if bit_match:
            indent = bit_match.group("indent")
            name = bit_match.group("name")
            suffix = bit_match.group("suffix") or ""
            scalar_bit_names.add(name)
            normalized_lines.append(f"{indent}bit[1] {name};{suffix}")
            continue

        normalized_lines.append(line)
    if scalar_bit_names:
        rewritten_lines: list[str] = []
        for line in normalized_lines:
            match = IF_SCALAR_BIT_COND_PATTERN.match(line)
            if not match:
                rewritten_lines.append(line)
                continue
            expr_raw = match.group("expr")
            negated = expr_raw.strip().startswith("!")
            name = expr_raw.strip()[1:].strip() if negated else expr_raw.strip()
            if name not in scalar_bit_names:
                rewritten_lines.append(line)
                continue
            compare = f"{name} == 0" if negated else f"{name} == 1"
            rewritten_lines.append(f"{match.group('prefix')}{compare}{match.group('suffix')}")
        normalized_lines = rewritten_lines

    return "\n".join(normalized_lines)

def rewrite_bit_to_bool_cast(lines: list[str], enabled: bool, spans: list[RewriteSpan], source: str) -> list[str]:
    if not enabled:
        return lines

    bit_names = {match.group(1) for match in BIT_DECL_PATTERN.finditer(source)}
    if not bit_names:
        return lines

    code_lines, _ = _comment_aware_code_and_spans(lines)
    rewritten_lines: list[str] = []
    for line_no, line in enumerate(lines, start=1):
        code_only = code_lines[line_no - 1].rstrip()
        match = BIT_IF_CAST_PATTERN.match(code_only)
        if not match:
            rewritten_lines.append(line)
            continue

        expr = match.group("expr").strip()
        base_name = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", expr)
        if not base_name or base_name.group(1) not in bit_names:
            rewritten_lines.append(line)
            continue

        prefix = match.group("prefix")
        suffix = match.group("suffix")
        value = match.group("value")
        rewritten_expr = f"{'!' if value == '0' else ''}{expr}"
        rewritten_code = f"{prefix}{rewritten_expr}{suffix}"
        tail = line[len(code_only):] if len(line) >= len(code_only) else ""
        rewritten_line = f"{rewritten_code}{tail}"
        spans.append(RewriteSpan(line_no, line, rewritten_expr, 7, "Rewrote bit comparison to a boolean cast."))
        rewritten_lines.append(rewritten_line)

    return rewritten_lines


def _parse_static_range(expr: str) -> list[int] | None:
    parts = [part.strip() for part in expr.split(":")]
    try:
        if len(parts) == 2:
            start = int(parts[0])
            end = int(parts[1])
            step = 1 if end >= start else -1
        elif len(parts) == 3:
            start = int(parts[0])
            step = int(parts[1])
            end = int(parts[2])
            if step == 0:
                return None
        else:
            return None
    except ValueError:
        return None

    if step > 0:
        return list(range(start, end + 1, step))
    return list(range(start, end - 1, step))


def _rewrite_uint_index_uses(line: str, uint_consts: dict[str, tuple[int, int]]) -> str:
    rewritten = line
    for name, (width, value) in uint_consts.items():
        pattern = re.compile(rf"\b{re.escape(name)}\s*\[\s*(-?\d+)\s*\]")

        def _replace(match: re.Match[str]) -> str:
            idx = int(match.group(1))
            bit_value = 0
            if 0 <= idx < width:
                bit_value = (value >> idx) & 1
            return str(bit_value)

        rewritten = pattern.sub(_replace, rewritten)

    rewritten = re.sub(r"\bbool\s*\(\s*0\s*\)", "false", rewritten)
    rewritten = re.sub(r"\bbool\s*\(\s*1\s*\)", "true", rewritten)
    return rewritten


def _fold_if_const_bool(line: str) -> list[str]:
    match = IF_CONST_BOOL_PATTERN.match(line)
    if not match:
        return [line]
    truthy = match.group("bool").lower() == "true"
    tail = match.group("tail").strip()
    indent = match.group("indent")
    if not truthy:
        return []
    if not tail:
        return []
    if tail.startswith("{") and tail.endswith("}"):
        inner = tail[1:-1].strip()
        if not inner:
            return []
        return [f"{indent}{inner}"]
    return [f"{indent}{tail}"]


def rewrite_uint_to_int(lines: list[str], enabled: bool, spans: list[RewriteSpan]) -> list[str]:
    if not enabled:
        return lines

    uint_consts: dict[str, tuple[int, int]] = {}
    code_lines, _ = _comment_aware_code_and_spans(lines)
    rewritten_lines: list[str] = []
    line_no = 1
    while line_no <= len(lines):
        line = lines[line_no - 1]
        code_line = code_lines[line_no - 1]
        code_only = code_line.rstrip()

        if not code_only.strip():
            rewritten_lines.append(line)
            line_no += 1
            continue

        const_decl = UINT_DECL_PATTERN.match(code_only)
        if const_decl:
            width = int(const_decl.group("width"))
            name = const_decl.group("name")
            value_text = (const_decl.group("value") or "").strip()
            if re.fullmatch(r"\d+", value_text):
                uint_consts[name] = (width, int(value_text))
                spans.append(RewriteSpan(line_no, line, "", 8, f"Folded uint constant `{name}` for importer compatibility."))
                line_no += 1
                continue
            rewritten_decl = f"{const_decl.group('indent')}bit[{width}] {name};"
            spans.append(RewriteSpan(line_no, line, rewritten_decl, 8, f"Rewrote uint declaration `{name}` to bit-array declaration."))
            rewritten_lines.append(rewritten_decl)
            line_no += 1
            continue

        single_line_loop = FOR_UINT_RANGE_PATTERN.match(code_only)
        if single_line_loop:
            loop_var = single_line_loop.group("var")
            values = _parse_static_range(single_line_loop.group("range"))
            body = single_line_loop.group("body").strip()
            if values is not None and body:
                emitted_lines: list[str] = []
                for value in values:
                    expanded = re.sub(rf"\b{re.escape(loop_var)}\b", str(value), body)
                    expanded = _rewrite_uint_index_uses(expanded, uint_consts)
                    for out_line in _fold_if_const_bool(expanded):
                        if out_line.strip():
                            emitted = f"{single_line_loop.group('indent')}{out_line.strip()}"
                            emitted_lines.append(emitted)
                            rewritten_lines.append(emitted)
                spans.append(RewriteSpan(line_no, line, "\n".join(emitted_lines), 8, f"Unrolled uint loop `{loop_var}` with static range."))
                line_no += 1
                continue

        loop_start = FOR_UINT_START_PATTERN.match(code_only)
        if loop_start:
            loop_var = loop_start.group("var")
            values = _parse_static_range(loop_start.group("range"))
            body_lines: list[str] = []
            scan_line = line_no + 1
            while scan_line <= len(lines):
                candidate = lines[scan_line - 1]
                candidate_code = code_lines[scan_line - 1].strip()
                if candidate_code == "}":
                    break
                body_lines.append(candidate)
                scan_line += 1
            if values is not None and body_lines and scan_line <= len(lines):
                emitted_lines: list[str] = []
                for value in values:
                    for body_line in body_lines:
                        expanded = re.sub(rf"\b{re.escape(loop_var)}\b", str(value), body_line)
                        expanded = _rewrite_uint_index_uses(expanded, uint_consts)
                        for out_line in _fold_if_const_bool(expanded):
                            if out_line.strip():
                                emitted_lines.append(out_line)
                                rewritten_lines.append(out_line)
                spans.append(RewriteSpan(line_no, line, "\n".join(emitted_lines), 8, f"Unrolled uint loop `{loop_var}` with static range."))
                line_no = scan_line + 1
                continue

        rewritten = _rewrite_uint_index_uses(code_only, uint_consts)
        rewritten = re.sub(r"\bbool\s*\(\s*([A-Za-z_][A-Za-z0-9_]*\s*\[[^\]]+\])\s*\)", r"\1", rewritten)
        folded_lines = _fold_if_const_bool(rewritten)
        if len(folded_lines) == 1:
            tail = line[len(code_only):] if len(line) >= len(code_only) else ""
            folded_lines = [f"{folded_lines[0]}{tail}"]
        if rewritten != code_only or len(folded_lines) != 1 or folded_lines[0] != line:
            spans.append(RewriteSpan(line_no, line, "\n".join(folded_lines), 8, "Applied uint compatibility rewrite."))
        for out_line in folded_lines:
            if out_line.strip() or line.strip():
                rewritten_lines.append(out_line)
        line_no += 1

    return rewritten_lines


def original_line_rule_matches(source: str) -> dict[int, list[tuple[int, str, int, int]]]:
    lines = normalize_lines(source)
    matches: dict[int, list[tuple[int, str, int, int]]] = defaultdict(list)
    code_lines, comment_spans = _comment_aware_code_and_spans(lines)
    bit_names = {match.group(1) for match in BIT_DECL_PATTERN.finditer(source)}
    colliding_gate_names: set[str] = set()
    for code_line in code_lines:
        gate_match = GATE_DEF_PATTERN.match(code_line)
        if gate_match and gate_match.group(1) in STDGATE_NAMES:
            colliding_gate_names.add(gate_match.group(1))

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            matches[line_no].append((2, "Drop blank lines", 0, 0))
            continue

        pragma_match = DQC_PRAGMA_PATTERN.match(line)
        if pragma_match:
            matches[line_no].append((6, "Split-generated teleportations", 0, len(line)))

        for start, end in comment_spans.get(line_no, []):
            matches[line_no].append((1, "Drop comments", start, end))

        code_only = code_lines[line_no - 1]

        for gate_name in sorted(colliding_gate_names):
            pattern = re.compile(rf"\b{re.escape(gate_name)}\b")
            for match in pattern.finditer(code_only):
                matches[line_no].append((5, "Rename colliding gates", match.start(), match.end()))

        cast_match = BIT_IF_CAST_PATTERN.match(code_only.rstrip())
        if cast_match and bit_names:
            expr = cast_match.group("expr").strip()
            base_name = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", expr)
            if base_name and base_name.group(1) in bit_names:
                matches[line_no].append((7, "Bit-to-bool Cast", cast_match.start("expr"), cast_match.end("value")))

        for uint_match in UINT_TOKEN_PATTERN.finditer(code_only):
            matches[line_no].append((8, "Uint Workaround", uint_match.start(), uint_match.end()))

    return matches


def add_split_markers(lines: list[str], split_lines: set[int]) -> str:
    out: list[str] = []
    next_id = 1
    for line_no, line in enumerate(lines, start=1):
        if line_no in split_lines:
            out.append(f"pragma dqc.v1.split id={next_id}")
            next_id += 1
        out.append(line)
    return "\n".join(out)


def split_generated_teleportations(next_chunk_index: int, incoming_sources: dict[str, set[int]] | None, qubit_register_names: set[str] | None = None) -> list[str]:
    incoming_sources = incoming_sources or {}
    qubit_register_names = qubit_register_names or set()
    dependencies: list[tuple[int, str]] = []
    barrier_targets: set[str] = set()
    for name, sources in incoming_sources.items():
        base_name = re.sub(r"\s*\[[^\]]+\]\s*$", "", name.strip())
        if base_name in qubit_register_names:
            barrier_targets.add(base_name)
        for source in sources:
            dependencies.append((int(source), name))
    dependencies.sort(key=lambda item: (item[0], item[1]))

    barrier_line = f"barrier {', '.join(sorted(barrier_targets))};" if barrier_targets else "barrier;"
    lines = [barrier_line, f"/* Teleporting qubits into chunk {next_chunk_index}:"]
    if dependencies:
        for source, name in dependencies:
            lines.append(f" * {name} from chunk {source}")
    else:
        lines.append(f" * no shared qubits from chunk {next_chunk_index - 1}")
    lines.append(" */")
    lines.append(barrier_line)
    return lines


def render_dqc_text(raw_text: str, split_before_lines: set[int]) -> str:
    lines = raw_text.splitlines(keepends=True)
    if not split_before_lines:
        return raw_text

    split_after_sorted = sorted({line_no - 1 for line_no in split_before_lines if line_no > 1})
    split_idx = 0
    pragma_id = 1
    current_chunk: list[str] = []
    rendered: list[str] = []

    for line_no, line in enumerate(lines, start=1):
        current_chunk.append(line)
        if split_idx < len(split_after_sorted) and line_no == split_after_sorted[split_idx]:
            rendered.append("".join(current_chunk))
            rendered.append(f"pragma dqc.v1.split id={pragma_id}\n")
            current_chunk = []
            split_idx += 1
            pragma_id += 1

    if current_chunk:
        rendered.append("".join(current_chunk))

    return "".join(rendered)


def split_pragma_line_numbers(text: str) -> set[int]:
    return {index for index, line in enumerate(text.splitlines(), start=1) if DQC_PRAGMA_PATTERN.match(line)}


def split_points_from_source(text: str) -> set[int]:
    split_points: set[int] = set()
    stripped_line_count = 0
    for line in text.splitlines():
        if DQC_PRAGMA_PATTERN.match(line):
            split_points.add(stripped_line_count + 1)
            continue
        stripped_line_count += 1
    return split_points


def normalize_dqc_clicked_split_line(source_text: str, clicked_line: int) -> int:
    pragma_lines = split_pragma_line_numbers(source_text)
    if clicked_line in pragma_lines:
        return clicked_line
    if clicked_line > 1 and clicked_line - 1 in pragma_lines:
        return clicked_line - 1
    return clicked_line


def extract_declarations(source: str) -> set[str]:
    names: set[str] = set()
    for match in DECL_PATTERN.finditer(source):
        names.add(match.group(1))
    return names


def extract_identifiers(source: str) -> set[str]:
    reserved = {"OPENQASM", "include", "input", "output", "const", "qubit", "bit", "int", "float", "bool", "array", "let", "gate", "measure", "reset", "if", "for", "while", "switch", "case", "default", "pragma", "dqc", "v1", "split"}
    return {token for token in IDENT_PATTERN.findall(source) if token not in reserved and not token.isupper()}


def extract_qubit_register_names(source: str) -> set[str]:
    names: set[str] = set()
    for line in normalize_lines(source):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.match(r"^\s*qubit(?:\[[^\]]+\])?\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if match:
            names.add(match.group(1))
    return names


def build_distributed_qasm(source: str, split_lines: set[int], chunk_flows: list[ChunkFlow] | None = None) -> tuple[str, str]:
    lines = normalize_lines(source)
    dqc_source = add_split_markers(lines, split_lines)
    qubit_register_names = extract_qubit_register_names(source)

    if chunk_flows is None:
        chunk_texts = split_dqc_chunks(dqc_source)
        chunk_flows = compute_chunk_flows(chunk_texts, source)

    generated: list[str] = []
    split_lines_sorted = sorted(split_lines)
    split_idx = 0
    for line_no, line in enumerate(lines, start=1):
        if split_idx < len(split_lines_sorted) and line_no == split_lines_sorted[split_idx]:
            next_chunk_index = split_idx + 2
            incoming_sources: dict[str, set[int]] = {}
            if 1 <= next_chunk_index <= len(chunk_flows):
                incoming_sources = chunk_flows[next_chunk_index - 1].incoming_sources
            generated.extend(split_generated_teleportations(next_chunk_index, incoming_sources, qubit_register_names))
            split_idx += 1
        generated.append(line)
    dqc_qasm = "\n".join(generated)
    return dqc_source, dqc_qasm


def split_dqc_chunks(text: str) -> list[str]:
    chunks: list[list[str]] = [[]]
    for line in text.splitlines():
        if DQC_PRAGMA_PATTERN.match(line):
            chunks.append([])
            continue
        chunks[-1].append(line)
    chunk_texts = ["\n".join(chunk) for chunk in chunks]
    if len(chunk_texts) == 1 and not chunk_texts[0]:
        return [""]
    return [chunk for chunk in chunk_texts if chunk or len(chunk_texts) == 1]


def prepare_chunk_text_for_run(chunk_text: str, source_text: str) -> str:
    if not chunk_text:
        return chunk_text
    if not OPENQASM_3_1_HEADER_RE.search(source_text):
        return chunk_text
    prefix_parts: list[str] = []
    if not OPENQASM_3_1_HEADER_RE.search(chunk_text):
        prefix_parts.append("OPENQASM 3.1;")
    if not STDGATES_INCLUDE_RE.search(chunk_text):
        prefix_parts.append('include "stdgates.inc";')
    if not prefix_parts:
        return chunk_text
    return "\n".join(prefix_parts) + "\n" + chunk_text


def _identifier_name(node: Any) -> str:
    if node is None:
        return ""
    kind_name = type(node).__name__
    if kind_name == "Identifier":
        return getattr(node, "name", "") or ""
    if kind_name == "IndexedIdentifier":
        base = getattr(node, "name", None)
        return getattr(base, "name", "") or ""
    return ""


def _node_identifier_names(node: Any) -> set[str]:
    names: set[str] = set()
    if node is None:
        return names
    for nested in _iter_ast_nodes(node):
        name = _identifier_name(nested)
        if name:
            names.add(name)
    return names


def _operand_identifier_names(node: Any) -> set[str]:
    name = _identifier_name(node)
    if name:
        return {name}
    return _node_identifier_names(node)


def _as_iterable_nodes(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _stmt_defined_names(stmt: Any) -> set[str]:
    kind_name = type(stmt).__name__
    if kind_name == "QubitDeclaration":
        name_obj = getattr(stmt, "identifier", None) or getattr(stmt, "qubit", None)
        name = getattr(name_obj, "name", "") or ""
        return {name} if name else set()
    if kind_name in {"ClassicalDeclaration", "IODeclaration"}:
        name = getattr(getattr(stmt, "identifier", None), "name", "") or ""
        return {name} if name else set()
    if kind_name == "AliasStatement":
        name = getattr(getattr(stmt, "target", None), "name", "") or ""
        return {name} if name else set()
    if kind_name == "QuantumMeasurementStatement":
        target = getattr(stmt, "target", None)
        name = _identifier_name(target)
        return {name} if name else set()
    if kind_name == "ClassicalAssignment":
        name = _identifier_name(getattr(stmt, "lvalue", None))
        return {name} if name else set()
    if kind_name in {"QuantumGateDefinition", "SubroutineDefinition", "CalibrationDefinition"}:
        name = getattr(getattr(stmt, "name", None), "name", "") or getattr(getattr(stmt, "identifier", None), "name", "") or ""
        return {name} if name else set()
    return set()


def _stmt_read_write_names(stmt: Any) -> tuple[set[str], set[str]]:
    kind_name = type(stmt).__name__
    if kind_name in {"QuantumGateDefinition", "SubroutineDefinition", "CalibrationDefinition"}:
        return set(), set()

    if kind_name == "ClassicalDeclaration":
        name = getattr(getattr(stmt, "identifier", None), "name", "") or ""
        reads = _operand_identifier_names(getattr(stmt, "init_expression", None))
        writes = {name} if name else set()
        return reads, writes

    if kind_name == "IODeclaration":
        name = getattr(getattr(stmt, "identifier", None), "name", "") or ""
        return set(), ({name} if name else set())

    if kind_name == "AliasStatement":
        target = _identifier_name(getattr(stmt, "target", None))
        reads = _operand_identifier_names(getattr(stmt, "value", None))
        writes = {target} if target else set()
        return reads, writes

    if kind_name == "ClassicalAssignment":
        reads = _operand_identifier_names(getattr(stmt, "rvalue", None))
        writes = _operand_identifier_names(getattr(stmt, "lvalue", None))
        return reads - writes, writes

    if kind_name == "QuantumGate":
        qubit_names: set[str] = set()
        for qb in _as_iterable_nodes(getattr(stmt, "qubits", None)):
            qubit_names |= _operand_identifier_names(qb)
        reads = qubit_names.copy()
        for arg in _as_iterable_nodes(getattr(stmt, "arguments", None)):
            reads |= _operand_identifier_names(arg)
        return reads, qubit_names

    if kind_name == "QuantumMeasurementStatement":
        measure = getattr(stmt, "measure", None)
        qubit_names = _operand_identifier_names(getattr(measure, "qubit", None))
        target_names = _operand_identifier_names(getattr(stmt, "target", None))
        reads = qubit_names.copy()
        writes = qubit_names | target_names
        return reads, writes

    if kind_name == "QuantumReset":
        qubit_names: set[str] = set()
        for qb in _as_iterable_nodes(getattr(stmt, "qubits", None)):
            qubit_names |= _operand_identifier_names(qb)
        return qubit_names.copy(), qubit_names

    if kind_name == "BranchingStatement":
        return _operand_identifier_names(getattr(stmt, "condition", None)), set()

    if kind_name == "WhileLoop":
        return _operand_identifier_names(getattr(stmt, "while_condition", None)), set()

    if kind_name == "ForInLoop":
        reads = _operand_identifier_names(getattr(stmt, "set_declaration", None))
        writes = _operand_identifier_names(getattr(stmt, "identifier", None))
        return reads - writes, writes

    if kind_name == "Box":
        return set(), set()

    reads: set[str] = set()
    for node in _iter_ast_nodes(stmt):
        name = _identifier_name(node)
        if name:
            reads.add(name)
    writes = _stmt_defined_names(stmt)
    return reads - writes, writes


def _scan_statement_dependencies(
    stmt: Any,
    chunk_index: int,
    current_writers: dict[str, int],
    incoming_sources: dict[str, set[int]],
    outgoing_targets: dict[int, dict[str, set[int]]],
    defined: set[str],
    used: set[str],
) -> None:
    kind_name = type(stmt).__name__
    if kind_name in {"QuantumGateDefinition", "SubroutineDefinition", "CalibrationDefinition"}:
        return

    if kind_name == "BranchingStatement":
        condition_used = _node_identifier_names(getattr(stmt, "condition", None))
        used.update(condition_used)
        for name in sorted(condition_used):
            writer = current_writers.get(name)
            if writer is not None and writer != chunk_index:
                incoming_sources.setdefault(name, set()).add(writer)
                outgoing_targets.setdefault(writer, {}).setdefault(name, set()).add(chunk_index)
        for inner in getattr(stmt, "if_block", []) or []:
            _scan_statement_dependencies(inner, chunk_index, current_writers, incoming_sources, outgoing_targets, defined, used)
        for inner in getattr(stmt, "else_block", []) or []:
            _scan_statement_dependencies(inner, chunk_index, current_writers, incoming_sources, outgoing_targets, defined, used)
        return

    if kind_name == "WhileLoop":
        condition_used = _node_identifier_names(getattr(stmt, "while_condition", None))
        used.update(condition_used)
        for name in sorted(condition_used):
            writer = current_writers.get(name)
            if writer is not None and writer != chunk_index:
                incoming_sources.setdefault(name, set()).add(writer)
                outgoing_targets.setdefault(writer, {}).setdefault(name, set()).add(chunk_index)
        for inner in getattr(stmt, "block", []) or []:
            _scan_statement_dependencies(inner, chunk_index, current_writers, incoming_sources, outgoing_targets, defined, used)
        return

    if kind_name == "Box":
        for inner in getattr(stmt, "body", []) or []:
            _scan_statement_dependencies(inner, chunk_index, current_writers, incoming_sources, outgoing_targets, defined, used)
        return

    stmt_used, stmt_defined = _stmt_read_write_names(stmt)
    used.update(stmt_used)
    defined.update(stmt_defined)

    for name in sorted(stmt_used):
        writer = current_writers.get(name)
        if writer is not None and writer != chunk_index:
            incoming_sources.setdefault(name, set()).add(writer)
            outgoing_targets.setdefault(writer, {}).setdefault(name, set()).add(chunk_index)

    for name in sorted(stmt_defined):
        current_writers[name] = chunk_index


def compute_chunk_flows(chunk_texts: list[str], source_text: str) -> list[ChunkFlow]:
    current_writers: dict[str, int] = {}
    flows: list[ChunkFlow] = []
    outgoing_by_source: dict[int, dict[str, set[int]]] = {}

    for index, chunk_text in enumerate(chunk_texts, 1):
        defined: set[str] = set()
        used: set[str] = set()
        incoming_sources: dict[str, set[int]] = {}
        prepared = prepare_chunk_text_for_run(chunk_text, source_text)
        try:
            program = safe_import_qasm3()(prepared)
        except Exception:
            program = None

        if program is not None:
            for stmt in getattr(program, "statements", []):
                _scan_statement_dependencies(stmt, index, current_writers, incoming_sources, outgoing_by_source, defined, used)

        flows.append(
            ChunkFlow(
                title=f"Chunk {index}",
                original_text=chunk_text,
                rewritten_text="",
                defined=defined,
                used=used,
                incoming_sources=incoming_sources,
                outgoing_targets={},
            )
        )

    for index, flow in enumerate(flows, 1):
        flow.outgoing_targets = outgoing_by_source.get(index, {})

    return flows


def build_chunk_dependency_graph(flows: list[ChunkFlow]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for index, flow in enumerate(flows, 1):
        graph.add_node(index, label=flow.title, defined=sorted(flow.defined), used=sorted(flow.used))

    edge_labels: dict[tuple[int, int], set[str]] = {}
    for index, flow in enumerate(flows, 1):
        for name, sources in flow.incoming_sources.items():
            for source in sources:
                if source == index:
                    continue
                edge_labels.setdefault((source, index), set()).add(name)

    for (source, dest), labels in edge_labels.items():
        graph.add_edge(source, dest, label=", ".join(sorted(labels)))

    return graph


def _heuristic_split_points(source: str, max_points: int) -> tuple[list[int], str]:
    lines = normalize_lines(source)
    scores: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if stripped.startswith(("OPENQASM", "include", "bit ", "qubit ", "input ", "output ", "const ")):
            continue
        qubits = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\[[^\]]+\]", stripped)
        multi_qubit = max(0, len(qubits) - 1)
        control_flow = 2 if re.match(r"^(if|for|while|switch)\b", stripped) else 0
        declaration_jump = 1 if re.match(r"^(gate|extern|def|defcal)\b", stripped) else 0
        score = multi_qubit * 4 + control_flow + declaration_jump
        if score > 0:
            scores.append((score, line_no, stripped[:80]))
    if not scores:
        return [], "No strong split boundaries were detected; the heuristic prefers multi-qubit boundaries and control-flow transitions."
    scores.sort(key=lambda item: (-item[0], item[1]))
    selected = sorted(line_no for _, line_no, _ in scores[:max_points])
    reason = ", ".join(f"line {line_no}" for line_no in selected)
    return selected, f"Heuristic split suggestions based on interaction density and control-flow boundaries: {reason}."


def _resolve_kahypar_ini() -> Path | None:
    if _kahypar is None:
        return None
    module_file = getattr(_kahypar, "__file__", None)
    if not module_file:
        return None
    base = Path(module_file).resolve().parent
    candidates = sorted(base.rglob("*.ini"))
    if not candidates:
        return None
    preferred = [c for c in candidates if "cut" in c.name.lower()]
    return preferred[0] if preferred else candidates[0]


def _kahypar_partition(vertex_count: int, hyperedges: list[list[int]], edge_weights: list[int], k: int) -> list[int] | None:
    if _kahypar is None or vertex_count == 0 or k <= 1:
        return None
    if not hyperedges or len(hyperedges) != len(edge_weights):
        return None

    # KaHyPar expects strictly positive hyperedge weights; sanitize defensively.
    filtered_edges: list[list[int]] = []
    filtered_weights: list[int] = []
    for edge, weight in zip(hyperedges, edge_weights):
        unique_edge = sorted(set(int(v) for v in edge if 0 <= int(v) < vertex_count))
        if len(unique_edge) < 2:
            continue
        filtered_edges.append(unique_edge)
        filtered_weights.append(max(1, int(weight)))

    if not filtered_edges:
        return None

    flattened: list[int] = []
    edge_index: list[int] = [0]
    for edge in filtered_edges:
        flattened.extend(edge)
        edge_index.append(len(flattened))

    hypergraph = None
    signatures: list[tuple[Any, ...]] = [
        # Preferred ordering from KaHyPar Python bindings:
        # num_nodes, num_hyperedges, hyperedge_indices, hyperedges, k, edge_weights, node_weights
        (vertex_count, len(filtered_edges), edge_index, flattened, k, filtered_weights, [1] * vertex_count),
        # Fallback variant seen in some builds.
        (vertex_count, len(filtered_edges), edge_index, flattened, k, [1] * vertex_count, filtered_weights),
        (vertex_count, len(filtered_edges), edge_index, flattened, k, filtered_weights),
        (vertex_count, len(filtered_edges), edge_index, flattened, k),
    ]
    for args in signatures:
        try:
            hypergraph = _kahypar.Hypergraph(*args)
            break
        except Exception:
            hypergraph = None
    if hypergraph is None:
        return None

    try:
        context = _kahypar.Context()
    except Exception:
        return None

    try:
        if hasattr(context, "suppressOutput"):
            context.suppressOutput(True)
        if hasattr(context, "setK"):
            context.setK(k)
        if hasattr(context, "setSeed"):
            context.setSeed(42)
        if hasattr(context, "setEpsilon"):
            context.setEpsilon(0.03)
        if hasattr(context, "loadINIconfiguration"):
            ini_file = _resolve_kahypar_ini()
            if ini_file is not None:
                context.loadINIconfiguration(str(ini_file))
        if hasattr(_kahypar, "Objective") and hasattr(context, "setObjective"):
            objective = getattr(_kahypar.Objective, "cut", None)
            if objective is not None:
                context.setObjective(objective)
    except Exception:
        return None

    try:
        _kahypar.partition(hypergraph, context)
    except Exception:
        return None

    try:
        return [int(hypergraph.blockID(index)) for index in range(vertex_count)]
    except Exception:
        return None


def suggest_split_points(source: str, max_points: int | None = None, distributed_nodes: int = 3) -> tuple[list[int], str]:
    distributed_nodes = max(1, min(8, int(distributed_nodes)))
    target_points = distributed_nodes - 1
    if max_points is not None:
        target_points = min(target_points, max(0, int(max_points)))
    if target_points <= 0:
        return [], f"Distributed split suggestions disabled for {distributed_nodes} QPU node(s): at least 2 nodes are required."

    lines = normalize_lines(source)
    code_lines, _ = _comment_aware_code_and_spans(lines)
    executable_lines: list[int] = []
    line_identifiers: dict[int, set[str]] = {}

    reserved_tokens = {
        "OPENQASM",
        "include",
        "pragma",
        "if",
        "for",
        "while",
        "switch",
        "case",
        "default",
        "gate",
        "def",
        "defcal",
        "measure",
        "reset",
    }

    for line_no, code_only in enumerate(code_lines, start=1):
        stripped = code_only.strip()
        if not stripped:
            continue
        if stripped.startswith(("OPENQASM", "include", "pragma ", "//", "/*", "*", "*/")):
            continue
        if stripped in {"{", "}", "};"}:
            continue
        if re.match(r"^(qubit|bit|int|uint|float|bool|array|const|input|output)\b", stripped):
            continue
        executable_lines.append(line_no)
        line_identifiers[line_no] = {token for token in IDENT_PATTERN.findall(stripped) if token not in reserved_tokens}

    if len(executable_lines) < 2:
        return [], "Not enough executable statements to suggest split points."

    identifier_to_vertices: dict[str, list[int]] = defaultdict(list)
    for vertex, line_no in enumerate(executable_lines):
        for name in line_identifiers.get(line_no, set()):
            identifier_to_vertices[name].append(vertex)

    if not identifier_to_vertices:
        return _heuristic_split_points(source, min(target_points, 3))

    qubit_names = {match.group(1) for match in re.finditer(r"^\s*qubit(?:\[[^\]]+\])?\s+([A-Za-z_][A-Za-z0-9_]*)", source, re.MULTILINE)}
    bit_names = {match.group(1) for match in re.finditer(r"^\s*bit(?:\[[^\]]+\])?\s+([A-Za-z_][A-Za-z0-9_]*)", source, re.MULTILINE)}

    hyperedges: list[list[int]] = []
    edge_weights: list[int] = []
    for name, vertices in sorted(identifier_to_vertices.items()):
        unique_vertices = sorted(set(vertices))
        if len(unique_vertices) < 2:
            continue
        hyperedges.append(unique_vertices)
        if name in qubit_names:
            edge_weights.append(12)
        elif name in bit_names:
            edge_weights.append(4)
        else:
            edge_weights.append(2)

    if not hyperedges:
        return _heuristic_split_points(source, min(target_points, 3))

    chain_weight = max(8, sum(edge_weights) // max(1, len(edge_weights)))
    for left in range(len(executable_lines) - 1):
        hyperedges.append([left, left + 1])
        edge_weights.append(chain_weight)

    k = min(distributed_nodes, len(executable_lines))
    partition = _kahypar_partition(len(executable_lines), hyperedges, edge_weights, k)
    if partition is None:
        selected, reason = _heuristic_split_points(source, min(target_points, 3))
        return selected, f"KaHyPar unavailable; {reason}"

    boundary_candidates: list[int] = []
    for idx in range(len(executable_lines) - 1):
        if partition[idx] != partition[idx + 1]:
            candidate = executable_lines[idx + 1]
            if 1 < candidate <= len(lines):
                boundary_candidates.append(candidate)

    if not boundary_candidates:
        selected, reason = _heuristic_split_points(source, min(target_points, 3))
        return selected, f"KaHyPar returned no contiguous cut boundary; {reason}"

    boundary_costs: list[tuple[int, int]] = []
    for candidate in sorted(set(boundary_candidates)):
        previous = max(1, candidate - 1)
        left_ids = line_identifiers.get(previous, set())
        right_ids = line_identifiers.get(candidate, set())
        overlap = left_ids & right_ids
        overlap_cost = 0
        for name in overlap:
            overlap_cost += 12 if name in qubit_names else 4 if name in bit_names else 2
        boundary_costs.append((overlap_cost, candidate))

    boundary_costs.sort(key=lambda item: (item[0], item[1]))
    selected = sorted(candidate for _, candidate in boundary_costs[:target_points])
    selected = [line for line in selected if not line_is_inside_blocking_scope(source, line)]
    if not selected:
        return [], f"KaHyPar selected split boundaries that all fall inside guarded scopes for {distributed_nodes} QPU nodes."
    reason = ", ".join(f"line {line_no}" for line_no in selected)
    return selected, f"KaHyPar hypergraph partitioning selected {len(selected)} split point(s) for {distributed_nodes} QPU node(s): {reason}."


def safe_import_qasm3():
    from openqasm3 import parse  # type: ignore

    return parse


def ast_to_tree(node: Any, label: str = "program", depth: int = 0) -> list[str]:
    if isinstance(node, (str, int, float, bool)) or node is None:
        return [f"{'  ' * depth}{label}: {node!r}"]
    lines = [f"{'  ' * depth}{label}: {type(node).__name__}"]
    if isinstance(node, dict):
        for key, value in node.items():
            lines.extend(ast_to_tree(value, str(key), depth + 1))
        return lines
    if isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            lines.extend(ast_to_tree(value, f"[{index}]", depth + 1))
        return lines
    fields = getattr(node, "__dict__", {})
    for key, value in fields.items():
        if key.startswith("_") or key in {"span"}:
            continue
        lines.extend(ast_to_tree(value, key, depth + 1))
    return lines


def qasm_token_graph(source: str) -> tuple[nx.DiGraph, nx.Graph, nx.DiGraph]:
    dag = nx.DiGraph()
    interaction = nx.Graph()
    chunk_graph = nx.DiGraph()
    lines = [line.strip() for line in normalize_lines(source) if line.strip()]
    op_id = 0
    current_chunk = 0
    chunk_use: dict[int, set[str]] = defaultdict(set)
    for line in lines:
        if line.startswith("pragma dqc.v1.split"):
            current_chunk += 1
            continue
        if line.startswith("/*") or line.startswith("*") or line.startswith("//") or line.startswith("*/"):
            continue
        op_id += 1
        node = f"op_{op_id}"
        dag.add_node(node, label=line, chunk=current_chunk)
        if op_id > 1:
            dag.add_edge(f"op_{op_id - 1}", node)
        if "(" in line or " " in line:
            tail = line.split(" ", 1)[1] if " " in line else line
            operands = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\b", tail)
            if len(operands) >= 2:
                for i in range(len(operands)):
                    for j in range(i + 1, len(operands)):
                        a, b = sorted((operands[i], operands[j]))
                        if a == b:
                            continue
                        if interaction.has_edge(a, b):
                            interaction[a][b]["weight"] += 1
                        else:
                            interaction.add_edge(a, b, weight=1)
                chunk_use[current_chunk].update(operands)
    chunk_ids = sorted(chunk_use)
    for left, right in zip(chunk_ids, chunk_ids[1:]):
        shared = sorted(chunk_use[left] & chunk_use[right])
        label = ", ".join(shared) if shared else "teleport bridge"
        chunk_graph.add_edge(left, right, label=label)
    return dag, interaction, chunk_graph


def run_on_aer(source: str, shots: int, parameter_bindings: dict[str, str] | None = None) -> RewriteResult:
    from qiskit_qasm3_import import parse as qiskit_parse
    from qiskit_aer import AerSimulator
    from qiskit import transpile

    start = time.perf_counter()
    runtime_source = normalize_scalar_register_declarations(source)
    circuit = qiskit_parse(runtime_source)
    circuit = _bind_circuit_parameters(circuit, parameter_bindings)
    backend = AerSimulator()
    compiled = transpile(circuit, backend)
    job = backend.run(compiled, shots=shots)
    result = job.result()
    counts = dict(result.get_counts())
    duration_s = time.perf_counter() - start
    return RewriteResult(source=source, rewritten_source=source, circuit=circuit, counts=counts, duration_s=duration_s)


def run_runtime_counts(runtime_source: str, parameter_bindings: dict[str, str] | None, shots: int) -> tuple[dict[str, int] | None, str | None, datetime]:
    run_timestamp = datetime.now(timezone.utc)
    try:
        from qiskit_qasm3_import import parse as qiskit_parse
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        circuit = qiskit_parse(normalize_scalar_register_declarations(runtime_source))
        circuit = _bind_circuit_parameters(circuit, parameter_bindings)
        backend = AerSimulator()
        compiled = transpile(circuit, backend)
        result = backend.run(compiled, shots=shots).result()
        return dict(result.get_counts()), None, run_timestamp
    except Exception as exc:
        return None, str(exc), run_timestamp


def rewrite_and_analyze(source: str, rules: list[RuleState], split_lines: set[int], parameter_bindings: dict[str, str] | None = None, shots: int = 1024, timeout_s: int = 10, execute_runtime: bool = True, distributed_nodes: int = 3) -> RewriteResult:
    parse = safe_import_qasm3()
    rule_map = {rule.rule_id: rule.enabled for rule in rules}
    bypass = rule_map.get(0, False)
    active_rule_ids = [] if bypass else sorted(rule_id for rule_id, enabled in rule_map.items() if enabled and rule_id != 0)
    spans: list[RewriteSpan] = []
    lines = normalize_lines(source)
    original_lines = list(lines)
    if bypass:
        rewritten = lines
    else:
        rewritten = lines
        for rule_id in active_rule_ids:
            if rule_id == 1:
                rewritten, kept_line_numbers = rewrite_comments_and_blanks_with_map(
                    rewritten,
                    True,
                    False,
                    spans,
                    original_lines=original_lines,
                )
                split_lines = remap_split_points(split_lines, kept_line_numbers)
            elif rule_id == 2:
                rewritten, kept_line_numbers = rewrite_comments_and_blanks_with_map(
                    rewritten,
                    False,
                    True,
                    spans,
                    original_lines=original_lines,
                )
                split_lines = remap_split_points(split_lines, kept_line_numbers)
            elif rule_id == 3:
                if not any(HEADER_PATTERN.match(line) for line in rewritten):
                    rewritten = maybe_add_header(rewritten, True, spans)
                    split_lines = shift_split_points(split_lines, 1, 1)
            elif rule_id == 4:
                if not any(INCLUDE_PATTERN.match(line) for line in rewritten):
                    insert_at = 1 if rewritten and HEADER_PATTERN.match(rewritten[0]) else 0
                    rewritten = maybe_add_include(rewritten, True, spans)
                    split_lines = shift_split_points(split_lines, insert_at + 1, 1)
            elif rule_id == 5:
                rewritten = rename_colliding_gates(rewritten, True, spans)
            elif rule_id == 7:
                rewritten = rewrite_bit_to_bool_cast(rewritten, True, spans, source)
            elif rule_id == 8:
                rewritten = rewrite_uint_to_int(rewritten, True, spans)
    rewritten_source = "\n".join(rewritten)
    dqc_source = add_split_markers(normalize_lines(rewritten_source), split_lines)
    chunk_texts = split_dqc_chunks(dqc_source)
    chunk_flows = compute_chunk_flows(chunk_texts, rewritten_source)
    _, dqc_qasm = build_distributed_qasm(rewritten_source, split_lines, chunk_flows=chunk_flows)
    apply_rule_6 = 6 in active_rule_ids
    display_rewritten_source = dqc_qasm if split_lines and apply_rule_6 else rewritten_source
    chunk_graph = build_chunk_dependency_graph(chunk_flows)
    parse_tree = None
    issues: list[RewriteSpan] = []
    try:
        # Keep AST spans aligned with what the Rewritten tab is actually showing.
        parse_tree = parse(display_rewritten_source)
    except Exception as exc:
        issues.append(RewriteSpan(1, source.splitlines()[0] if source.splitlines() else "", "", 0, f"QASM parse failed: {exc}", kind="error"))
    dag_graph, interaction_graph, _ = qasm_token_graph(rewritten_source)
    suggested_split_points, suggestion_reason = suggest_split_points(rewritten_source, distributed_nodes=distributed_nodes)
    circuit_result = None
    counts: dict[str, int] = {}
    duration_s = 0.0
    try:
        from qiskit_qasm3_import import parse as qiskit_parse
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        runtime_source = dqc_qasm
        circuit_result = qiskit_parse(normalize_scalar_register_declarations(runtime_source))
        if parameter_bindings:
            circuit_result = _bind_circuit_parameters(circuit_result, parameter_bindings)
        if execute_runtime:
            start = time.perf_counter()
            backend = AerSimulator()
            compiled = transpile(circuit_result, backend)
            job = backend.run(compiled, shots=shots)
            result = job.result(timeout=timeout_s)
            counts = dict(result.get_counts())
            duration_s = time.perf_counter() - start
    except Exception as exc:
        issues.append(RewriteSpan(1, source.splitlines()[0] if source.splitlines() else "", "", 0, f"Runtime execution failed: {exc}", kind="error"))
    return RewriteResult(source=source, rewritten_source=display_rewritten_source, spans=spans, issues=issues, parse_tree=parse_tree, circuit=circuit_result, counts=counts, duration_s=duration_s, split_source=dqc_source, split_qasm=dqc_qasm, chunk_flows=chunk_flows, chunk_graph=chunk_graph, interaction_graph=interaction_graph, dag_graph=dag_graph, ast_graph=nx.DiGraph(), suggested_split_points=suggested_split_points, suggestion_reason=suggestion_reason)


def build_ast_graph(parse_tree: Any) -> nx.DiGraph:
    graph = nx.DiGraph()
    counter = 0

    def visit(node: Any, parent: str | None = None, label: str = "root") -> str:
        nonlocal counter
        counter += 1
        node_id = f"ast_{counter}"
        if isinstance(node, (str, int, float, bool)) or node is None:
            graph.add_node(node_id, label=f"{label}: {node!r}")
        else:
            graph.add_node(node_id, label=f"{label}: {type(node).__name__}")
            fields = getattr(node, "__dict__", {})
            for key, value in fields.items():
                if key.startswith("_") or key in {"span"}:
                    continue
                if isinstance(value, (list, tuple)):
                    for idx, item in enumerate(value):
                        child = visit(item, node_id, f"{key}[{idx}]")
                        graph.add_edge(node_id, child)
                else:
                    child = visit(value, node_id, key)
                    graph.add_edge(node_id, child)
        if parent is not None:
            graph.add_edge(parent, node_id)
        return node_id

    visit(parse_tree)
    return graph


def package_versions(packages: Iterable[str] | None = None) -> dict[str, str]:
    if packages is None:
        packages = [
            "PySide6",
            "qiskit",
            "qiskit-aer",
            "qiskit-qasm3-import",
            "openqasm3",
            "antlr4-python3-runtime",
            "networkx",
            "matplotlib",
            "pylatexenc",
        ]
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not installed"
    return versions


def latest_versions_from_pypi(packages: Iterable[str]) -> dict[str, str]:
    updates: dict[str, str] = {}
    for package in packages:
        url = f"https://pypi.org/pypi/{package}/json"
        try:
            with urlopen(url, timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
            updates[package] = payload["info"]["version"]
        except (URLError, TimeoutError, KeyError, json.JSONDecodeError):
            updates[package] = "unavailable"
    return updates


def smoke_test_hadamard(shots: int = 256) -> dict[str, Any]:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    backend = AerSimulator()
    started = time.perf_counter()
    result = backend.run(circuit, shots=shots).result()
    duration_s = time.perf_counter() - started
    counts = dict(result.get_counts())
    return {"shots": shots, "duration_s": duration_s, "counts": counts, "circuit": circuit}


def summary_text(result: RewriteResult, shots: int) -> str:
    counts = Counter(result.counts)
    total = sum(counts.values()) or 1
    circuit = result.circuit
    width = getattr(circuit, "num_qubits", 0) if circuit is not None else 0
    depth = circuit.depth() if circuit is not None and hasattr(circuit, "depth") else 0
    size = circuit.size() if circuit is not None and hasattr(circuit, "size") else 0
    volume = width * max(depth, 1)
    lines = [
        f"Circuit summary: width={width} qubits, depth={depth} parallel steps, size={size} gates, volume={volume};",
        f"Runtime started at {result.started_at_utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC, duration {result.duration_s:0.3f}s, shots {shots};",
        "Measurement outcomes:",
        "  readings -> occurrences (share of shots)",
    ]
    if not counts:
        lines.append("  No measurement counts returned.")
    for reading, occurrences in counts.most_common():
        lines.append(f"  {reading:<8} -> {occurrences} ({occurrences / total:.2%})")
    return "\n".join(lines)