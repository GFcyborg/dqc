
python3 -m venv .venv
. .venv/bin/activate && \
	python -m pip install -r requirements.txt && \
	python -m app

echo Done with DQC in $PWD
sleep 10
