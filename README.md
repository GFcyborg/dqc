# dqc

Distributed Quantum Computing (DQC): a QASM3 workbench to simulate split execution over a mesh of nodes (one chunk per QPU).

## Quick Start

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run the app from the repository root:

```bash
python main.py
```

Alternative entrypoint:

```bash
python -m app
```

## Day-to-Day Commands

Run full tests with a hard timeout below 5 minutes:

```bash
timeout 280s python -m pytest -q
```

Run one focused test module:

```bash
python -m pytest -q tests/test_pipeline_regressions.py
```

Run one specific regression test:

```bash
python -m pytest -q tests/test_runtime_source_coherence_regression.py
```

## Paths and Generated Artifacts

- Start from the project root so relative paths resolve consistently.
- Built-in examples are under `qasm/`.
- Split-save artifacts are written under `qasm/split/<example-name>/`.
- The rewritten dump saved as `*.dqc.qasm` is expected to match the live Rewritten view for the active rule selection.

## Architecture at a Glance

- `app/pipeline.py`: headless rewrite/analyze/execute logic (rules, split/teleport analysis, graph data, AER runtime).
- `app/widgets.py`: Qt widgets for code views, graphs, circuit rendering, and diagnostics display.
- `app/main_window_clean.py`: top-level UI wiring (menus, actions, refresh pipeline, runtime orchestration).
- `app/main_window.py`: compatibility shim re-exporting the main window API.

Rule execution model:

- Conditional rules run in numeric order.
- Rule `0` bypasses conditional rules.
- Unconditional rules `98` and `99` run after conditional rules.
- Downstream consumers (Rewritten view, runtime, circuit, graphs) are designed to use the same rewritten source.

## Most Important Regression Tests

These are the highest-signal tests for core app behavior:

- `tests/test_pipeline_regressions.py`: rewrite pipeline order, fallbacks, and core transformations.
- `tests/test_runtime_source_coherence_regression.py`: runtime must consume the same rewritten source shown in UI paths.
- `tests/test_save_split_dump_regression.py`: saved `*.dqc.qasm` must match Rewritten view and reject internal-only markers.
- `tests/test_rewrite_spans.py`: rewrite span mapping and coloring anchors across rule interactions.
- `tests/test_rule11_measurement_consistency_regression.py`: rule #11 split-generated teleportation measurement coherence.
- `tests/test_chunk_edge_label_centering_regression.py`: chunk dependency edge-label placement stability.

## [Free Palestine!](https://en.wikipedia.org/wiki/Israeli-occupied_territories)
