from prefix_codes.codec import Codec
from prefix_codes.decoder import Decoder

if __name__ == '__main__':
    codec = Codec(codeword_table={
        'a': '00',
        'b': '01',
    })
    code = codec.encode('ab')
    print(code)
    decoder = Decoder(dict(a='00', b='01'))
    # print(decoder)
    for c in decoder.decode(bytes([2])):
        print(c)
    # print(decoded)

