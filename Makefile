.PHONY: encode_english
encode_english:
	python3.9 main.py huffman encode prefix_codes/tests/englishText.txt

.PHONY: decode_english
decode_english:
	python3.9 main.py huffman decode prefix_codes/tests/englishText.txt.enc

.PHONY: english
english: encode_english decode_english
	diff prefix_codes/tests/englishText.txt prefix_codes/tests/englishText_dec.txt

.PHONY: help
help:
	python3.9 main.py --help

.PHONY: test
test:
	python3.9 -m unittest prefix_codes.tests.tests
