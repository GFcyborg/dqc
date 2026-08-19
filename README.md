# dqc

Distributed Quantum Computing (DQC): a QASM3 workbench to simulate circuit split-execution over a mesh of nodes, 1 chunk per QPU.

## Quick Setup

1. Open a terminal in the repository root.
1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

1. Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

1. Start the app from the repository root:

```bash
python main.py
```

## Notes

- The app uses relative paths only. Run it from the repository root so the bundled `qasm/` examples and generated `qasm/split/` artifacts resolve correctly.
- The default example loads from `qasm/`.
- Save-split output is written under `qasm/split/<stem>/`.
- If you prefer, `python -m app` is equivalent to `python main.py`.

## Architecture

- `app/pipeline.py` — headless logic: rewriting rules, split/teleport analysis,
  graph building (DAG, qubit interaction, chunk dependencies), and Aer
  execution. No Qt imports; safe to unit test directly.
- `app/widgets.py` — Qt widgets (code editors, graph views, circuit/DAG
  rendering) that display data produced by `pipeline.py`.
- `app/main_window_clean.py` — the `MainWindow`, wiring menus/toolbars to the
  pipeline and widgets. `app/main_window.py` is a thin re-export shim kept for
  import-path stability.
- Rewriting rules are numbered and applied in order (see `DEFAULT_RULES` in
  `pipeline.py`); rule 0 bypasses all conditional rules, while rules 98
  (restore `++` alias concatenation) and 99 (comment out stray pragmas) are
  unconditional and always run last, after the conditional rules, so every
  downstream view (Rewritten tab, circuit, runtime, graphs) sees identical code.

## Tests

1. Activate the virtual environment from the repository root:

```bash
. .venv/bin/activate
```

1. Install dependencies (includes test dependencies):

```bash
python -m pip install -r requirements.txt
```

1. Run the regression suite:

```bash
python -m pytest -q
```
