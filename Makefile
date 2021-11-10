.PHONY: encode
encode:
	python3.9 main.py huffman encode prefix_codes/tests/englishText.txt > prefix_codes/tests/englishText.txt.enc

.PHONY: test_encode
test_encode:
	python3.9 main.py huffman encode prefix_codes/tests/englishText.txt

.PHONY: help
help:
	python3.9 main.py --help

.PHONY: test
test:
	python3.9 -m unittest prefix_codes.tests.tests
