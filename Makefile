.PHONY: main
main:
	python3.9 main.py

.PHONY: test
test:
	python3.9 -m unittest prefix_codes.tests.tests
