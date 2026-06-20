# dqc

Desktop QASM3 workbench built with PySide6.

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
- If you prefer, `python -m dqc_app` is equivalent to `python main.py`.
