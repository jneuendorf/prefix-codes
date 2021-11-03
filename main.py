from prefix_codes.codec import Codec
from prefix_codes.utils import read_bits

if __name__ == '__main__':
    codeword_table = {
        'a': '00',
        'b': '01',
        'c': '100',
        'd': '101',
        'e': '110',
        'f': '111',
    }
    words = [
        'a',  # => 00 == 0
        'ab',  # => 10 00 == 8
        'ffa',  # => 00 111 111 == 63
        'deadbeef',  # => 111 110 110 01 101 00 110 101 = 111110 11001101 00110101 == 62 205 53
        'bad cafe bad face bed fed'.replace(' ', ''),
    ]
    codec = Codec(codeword_table)
    print(codec.tree)

    for word in words:
        print('word:', word)
        encoded = codec.encode(word)
        print('encoded', ''.join(
            str(bit) for bit in reversed(list(read_bits(encoded)))
        ))
        processed_word = codec.decode(encoded, max_length=len(word))
        assert processed_word == word, (
            f'incorrect decoding: expected {word} but got {processed_word}'
        )

    invalid_message = 'invalid characters!'
    print('trying invalid message:', invalid_message)
    try:
        codec.encode('invalid characters!')
    except AssertionError as e:
        print(e)

