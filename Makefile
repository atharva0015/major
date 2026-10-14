.PHONY: test lint bench bench-healenium bench-healenium-live bench-shadow bench-api bench-golden bench-vision gates

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .
	mypy healing

bench:
	python -m scripts.bench
	python -m scripts.bench_verify

bench-healenium:
	python -m scripts.bench_healenium

bench-healenium-live:
	python -m scripts.bench_healenium_live

bench-shadow:
	python -m scripts.shadow_report

bench-api:
	python -m scripts.bench_api

bench-golden:
	python -m scripts.bench_golden

bench-vision:
	python -m scripts.bench_vision

gates:
	python -m scripts.check_gates
