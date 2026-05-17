#!/usr/bin/env python3
"""
Bai 3 - diablo2oo2 Crackme #09 Python keygen for lab/report use.
Default example: Name = TestUser.
"""
from __future__ import annotations
import argparse

ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def rol8(value: int, bits: int) -> int:
    value &= 0xFF
    bits %= 8
    return ((value << bits) | (value >> (8 - bits))) & 0xFF


def sanitize_name(name: str) -> str:
    return ''.join(ch for ch in name if ch in ALPHABET)


def rotate_table(table: str, offset: int) -> str:
    offset %= len(table)
    return table[offset:] + table[:offset]


def encrypt_name(name: str, rotated: str) -> str:
    if not name:
        return ''
    dl = rol8(ord(name[0]), 3)
    out = []
    for i, ch in enumerate(name):
        next_value = ord(name[i + 1]) if i + 1 < len(name) else 0
        al = ((ord(ch) ^ next_value) + dl) & 0xFF
        dl = (dl + al) & 0xFF
        out.append(rotated[al % len(rotated)])
    return ''.join(out)


def generate_serial(name: str) -> str:
    filtered = sanitize_name(name)
    if not filtered:
        return 'Invalid Username'
    offset = len(filtered) * 4
    if offset > 0x3C:
        offset = 0x1E
    rotated = rotate_table(ALPHABET, offset)
    encrypted = encrypt_name(filtered, rotated)
    serial = []
    for original_char, encrypted_char in zip(filtered, encrypted):
        enc_index = rotated.index(encrypted_char)
        rerotated = rotate_table(rotated, enc_index)
        original_index = rotated.index(original_char)
        serial.append(rerotated[original_index])
    return ''.join(serial)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='?', default='TestUser')
    args = parser.parse_args()
    print(f'Input name   : {args.name}')
    print(f'Filtered name: {sanitize_name(args.name) or "(empty)"}')
    print(f'Serial       : {generate_serial(args.name)}')


if __name__ == '__main__':
    main()
