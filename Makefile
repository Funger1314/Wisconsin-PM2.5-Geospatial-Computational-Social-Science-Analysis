PYTHON=.venv/bin/python

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

validate-data:
	$(PYTHON) -m src.pipeline validate

analysis:
	$(PYTHON) -m src.pipeline analysis

notebook:
	$(PYTHON) -m src.pipeline notebooks

test:
	$(PYTHON) -m pytest -q

slides:
	$(PYTHON) -m src.pipeline slides

report:
	$(PYTHON) -m src.pipeline report

all:
	$(PYTHON) -m src.pipeline all
