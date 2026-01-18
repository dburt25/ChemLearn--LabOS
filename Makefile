setup:
	python -m pip install --upgrade pip
	pip install -e .

run-demo:
	python scripts/create_demo_video.py --output data/demo.mp4
	scanner pipeline --input data/demo.mp4 --out output/demo-run

test:
	pytest -m scanner

lint:
	python -m py_compile $(shell rg --files -g '*.py' src/scanner)
