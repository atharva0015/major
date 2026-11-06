.PHONY: test lint bench bench-healenium bench-healenium-live bench-shadow bench-api bench-golden bench-golden-live bench-vision bench-decision bench-verify bench-heldout bench-demo-cases bench-e2e-live evidence-snapshot gates demo dashboard

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .
	mypy healing

bench:
	python -m scripts.bench
	python -m scripts.bench_verify

bench-verify:
	python -m scripts.bench_verify

bench-decision:
	python -m scripts.bench_decision

bench-heldout:
	python -m scripts.bench_heldout

bench-demo-cases:
	python -m scripts.bench_demo_cases

bench-e2e-live:
	python -m scripts.bench_e2e_live

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

bench-golden-live:
	python -m scripts.bench_golden_live

bench-vision:
	python -m scripts.bench_vision

evidence-snapshot:
	python -m scripts.evidence_snapshot

gates:
	python -m scripts.check_gates

demo:
	python -m scripts.demo

dashboard:
	python -m healing.dashboard.app
