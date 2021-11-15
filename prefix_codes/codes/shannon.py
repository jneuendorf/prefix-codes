# def shannon_code(codeword_table: dict[str, str], message: str) -> CodewordLenghts:
#     n = len(message)
#     counter = Counter(message)
#     relative_frequencies = {
#         terminal: count / n
#         for terminal, count in counter.items()
#     }
#     return {
#         terminal: ceil(-log2(relative_frequencies[terminal]))
#         for terminal in counter
#     }
