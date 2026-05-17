#!/usr/bin/env python3
"""
Bai 2 - errors_keygenme Python keygen for lab/report use.
Default example: Name = TestUser.
"""
from __future__ import annotations
import argparse

MASK32 = 0xFFFFFFFF


def u32(x: int) -> int:
    return x & MASK32


def rol32(x: int, n: int) -> int:
    n &= 31
    x &= MASK32
    return ((x << n) | (x >> (32 - n))) & MASK32


def ror32(x: int, n: int) -> int:
    n &= 31
    x &= MASK32
    return ((x >> n) | (x << (32 - n))) & MASK32


def bswap32(x: int) -> int:
    x &= MASK32
    return ((x & 0x000000FF) << 24) | ((x & 0x0000FF00) << 8) | \
           ((x & 0x00FF0000) >> 8) | ((x & 0xFF000000) >> 24)


def build_schedule(name: str) -> list[int]:
    raw = name.encode('latin-1')
    if len(raw) > 55:
        raise ValueError('This crackme implementation expects <= 55 bytes.')
    buf = bytearray(64)
    buf[:len(raw)] = raw
    buf[len(raw)] = 0x80
    buf[63] = (len(raw) << 3) & 0xFF
    words = []
    for i in range(16):
        words.append(bswap32(int.from_bytes(buf[i * 4:(i + 1) * 4], 'little')))
    for i in range(16, 96):
        words.append(rol32(words[i - 3] ^ words[i - 8] ^ words[i - 14] ^ words[i - 16], 1))
    return words


def generate_key(name: str) -> str:
    w = build_schedule(name)
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
    a, b, c, d, e = h
    for i in range(80):
        if i < 20:
            f, k = (b & c) | ((~b) & d), 0x5A827999
        elif i < 40:
            f, k = b ^ c ^ d, 0x6ED9EBA1
        elif i < 60:
            f, k = (b & c) | (b & d) | (c & d), 0x8F1BBCDC
        else:
            f, k = b ^ c ^ d, 0x0CA62C1D6
        temp = u32(rol32(a, 5) + f + e + k + w[i])
        e, d, c, b, a = d, c, ror32(b, 2), a, temp
    result = [u32(x + y) for x, y in zip(h, [a, b, c, d, e])]
    out = []
    for word in result:
        for byte in word.to_bytes(4, 'little'):
            n = byte & 0x0F
            out.append(chr(n + ord('0')) if n <= 9 else chr(n - 1 + ord('A')))
    return ''.join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='?', default='TestUser')
    args = parser.parse_args()
    print(f'Name  : {args.name}')
    print(f'Serial: {generate_key(args.name)}')


if __name__ == '__main__':
    main()
