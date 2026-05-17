#!/usr/bin/env python3
"""
Bai 4 - day-based keygen Python rewrite for lab/report use.
Default example: Name = TestUser, day = Sunday.

Note:
- Sunday is hard-coded and does not depend on name.
- Tuesday depends on CPUID in the original crackme. This script uses the CPUID
  values observed during this report; change CPUID_EAX0/CPUID_EAX1 to match
  another machine if needed.
- Saturday is very large in the original source and requires name length >= 13;
  for TestUser it is invalid, so this script reports that condition.
"""
from __future__ import annotations
import argparse
import hashlib

MASK32 = 0xFFFFFFFF
CPUID_EAX0 = (0x00000015, 0x756E6547, 0x6C65746E, 0x49656E69)  # eax, ebx, ecx, edx
CPUID_EAX1 = (0x000606A6, 0x14200800, 0xFEDA3223, 0x1F8BFBFF)  # eax, ebx, ecx, edx


def bswap32(x: int) -> int:
    return int.from_bytes((x & MASK32).to_bytes(4, 'little'), 'big')


def tohex_r_int(value: int, byte_len: int) -> str:
    return ''.join(f'{b:02X}' for b in (value & ((1 << (8 * byte_len)) - 1)).to_bytes(byte_len, 'little')[::-1])


def monday(name: str) -> str:
    b = name.encode('latin-1')
    if len(b) < 4:
        raise ValueError('Monday requires name length >= 4.')
    last = b[3] ^ 0x02
    if last == 0x7F:
        last = b[3] ^ 0x03
    return '<3<3' + chr(last)


def tuesday(name: str) -> str:
    b = name.encode('latin-1')
    if not b:
        raise ValueError('Tuesday requires a non-empty name.')
    expanded = bytearray(b[i % len(b)] for i in range(32))
    eax, ebx, ecx, edx = CPUID_EAX0
    xorval = (ebx ^ edx ^ bswap32(ecx)) & MASK32
    eax, ebx, ecx, edx = CPUID_EAX1
    xorval = (xorval ^ edx ^ ecx ^ bswap32(eax)) & MASK32
    b1, b2 = xorval & 0xFF, (xorval >> 8) & 0xFF
    xorval = (xorval & 0xFFFF0000) | (b1 << 8) | b2
    for i in range(8):
        w = int.from_bytes(expanded[i*4:i*4+4], 'little') ^ xorval
        expanded[i*4:i*4+4] = w.to_bytes(4, 'little')
    p2 = 0xB00B
    mul = 0
    for c in expanded:
        mul |= c
        mul = (mul * len(b)) & MASK32
        p2 = ((p2 ^ mul) << 4) & MASK32
        mul &= 0xFFFFFF00
    p2 = ((p2 >> 16) ^ p2) & 0xFFFF
    return 'T10-' + tohex_r_int(p2, 2)


def wednesday(name: str) -> str:
    b = name.encode('latin-1')
    if len(b) < 4:
        raise ValueError('Wednesday requires name length >= 4.')
    fsum = b[0] + b[1]
    ax = (fsum * fsum) & 0xFFFF
    al, ah = ax & 0xFF, (ax >> 8) & 0xFF
    al = ((al << 4) + b[2]) & 0xFF
    al ^= b[3]
    ax = (al * ah) & 0xFFFF
    al, ah = ax & 0xFF, (ax >> 8) & 0xFF
    al = ((al << 4) + b[2] + b[0]) & 0xFF
    ax = (ah << 8) | al
    answer = bswap32(ax) | ax
    return tohex_r_int(answer, 4)


def thursday(name: str) -> str:
    h = hashlib.md5(name.encode('latin-1')).digest()
    return (h[8:16] + h[:8]).hex().upper()


def friday(name: str) -> str:
    total = 1
    multi = 0
    for c in name.encode('latin-1'):
        total += c
        multi += total
    total %= 0xFFF1
    multi %= 0xFFF1
    nameval = ((multi << 16) + total) & MASK32
    return tohex_r_int(nameval, 4) + '-0400-0400-1229-03E9'


def saturday(name: str) -> str:
    if len(name) < 13:
        return 'Invalid: Saturday requires name length >= 13.'
    return 'Not implemented in this compact report script; original uses custom hash + Whirlpool + RIPEMD-256.'


def sunday(name: str | None = None) -> str:
    return 'A10-57617274-686F67'


def generate(name: str, day: str) -> str:
    funcs = {
        'monday': monday, 'tuesday': tuesday, 'wednesday': wednesday,
        'thursday': thursday, 'friday': friday, 'saturday': saturday,
        'sunday': sunday,
    }
    day = day.lower()
    if day not in funcs:
        raise ValueError('day must be one of: ' + ', '.join(funcs))
    return funcs[day](name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='?', default='TestUser')
    parser.add_argument('--day', default='sunday')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    if args.all:
        for d in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            print(f'{d.capitalize():9}: {generate(args.name, d)}')
    else:
        print(f'Name  : {args.name}')
        print(f'Day   : {args.day.capitalize()}')
        print(f'Serial: {generate(args.name, args.day)}')


if __name__ == '__main__':
    main()
