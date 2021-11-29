.PHONY: encode_english
encode_english:
	python3 main.py huffman encode prefix_codes/tests/englishText.txt

.PHONY: decode_english
decode_english:
	python3 main.py huffman decode prefix_codes/tests/englishText.txt.enc

.PHONY: english
english: encode_english decode_english
	diff prefix_codes/tests/englishText.txt prefix_codes/tests/englishText_dec.txt

.PHONY: encode_image
encode_image:
	python3 main.py huffman encode prefix_codes/tests/imageData.raw

.PHONY: decode_image
decode_image:
	python3 main.py huffman decode prefix_codes/tests/imageData.raw.enc

.PHONY: image
image: encode_image decode_image
	diff prefix_codes/tests/imageData.raw prefix_codes/tests/imageData_dec.raw

.PHONY: sfe
sfe:
	python3 main.py shannon-fano-elias encode prefix_codes/tests/imageData.raw


.PHONY: help
help:
	python3 main.py --help

.PHONY: test
test:
	python3 -m unittest prefix_codes.tests.tests

.PHONY: test2
test2:
	python3 -m unittest prefix_codes.tests.tests.TestCodecs.test_arithmetic_encode_decode

