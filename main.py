from prefix_codes.decoder import Decoder

if __name__ == '__main__':
    decoder = Decoder(dict(a='00', b='01'))
    # print(decoder)
    gen = decoder.decode(bytes([2]))
    for c in gen:
        print(c)
    # print(decoded)

