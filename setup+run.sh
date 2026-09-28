#!/bin/bash

# this script must be run from the project root-directory
if [ ! -f "$PWD/requirements.txt" ]; then
    echo "Run this script from the project root directory." >&2
    exit 1
fi

python3 -m venv .venv
. .venv/bin/activate && \
	python -m pip install -r requirements.txt && \
	python -m app

echo Done with DQC in $PWD ...
sleep 5
