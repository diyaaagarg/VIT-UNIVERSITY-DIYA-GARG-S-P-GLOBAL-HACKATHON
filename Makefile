PYTHON ?= .venv/bin/python

.PHONY: setup test ingest-demo analyze-demo evaluate rebalance-demo stress-demo simulate-breaking-news demo spacy-model
setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
	@echo "Setup complete. en_core_web_sm is optional; install it later with: make spacy-model"

spacy-model:
	.venv/bin/python -m spacy download en_core_web_sm

test:
	$(PYTHON) -m pytest -q

ingest-demo:
	$(PYTHON) -m src.ingestion.run --mode replay --speed instant

analyze-demo: ingest-demo
	$(PYTHON) -m src.engine.run

evaluate: analyze-demo
	$(PYTHON) -m src.evaluation.run

rebalance-demo: analyze-demo
	$(PYTHON) -m src.modules.rebalancer.run

stress-demo: analyze-demo
	$(PYTHON) -m src.modules.stress.run

simulate-breaking-news:
	$(PYTHON) -m src.modules.stress.simulate

demo: rebalance-demo stress-demo evaluate
	$(PYTHON) -m streamlit run src/dashboard/app.py
