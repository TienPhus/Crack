#!/usr/bin/env python3
"""
Bai 1 - KeygenMe1 Python keygen for lab/report use.
Default example uses ComputerName = LAPCUAPHU and Name = TestUser.
"""
from __future__ import annotations
import argparse

MASK = 0xFFFFFFFF


def rol(value: int, bits: int, width: int = 32) -> int:
    value &= (1 << width) - 1
    bits %= width
    return ((value << bits) | (value >> (width - bits))) & ((1 << width) - 1)


def ror(value: int, bits: int, width: int = 32) -> int:
    value &= (1 << width) - 1
    bits %= width
    return ((value >> bits) | (value << (width - bits))) & ((1 << width) - 1)


def bswap32(value: int) -> int:
    value &= MASK
    return ((value & 0x000000FF) << 24) | ((value & 0x0000FF00) << 8) | \
           ((value & 0x00FF0000) >> 8) | ((value & 0xFF000000) >> 24)


def computer_hash(computer_name: str) -> int:
    data = computer_name.encode('ascii', errors='ignore') + bytes(16)
    eax = edx = ebx = ecx = 0
    i = 0
    while (data[i] | (data[i + 1] << 8)) != 0:
        eax = (eax & 0xFFFFFF00) | data[i]
        edx = (edx & 0xFFFFFF00) | data[i + 1]
        al = ror(eax & 0xFF, 4, 8)
        eax = (eax & 0xFFFFFF00) | al
        dl = (~(edx & 0xFF)) & 0xFF
        edx = (edx & 0xFFFFFF00) | dl
        al = ((eax & 0xFF) + (edx & 0xFF)) & 0xFF
        eax = (eax & 0xFFFFFF00) | al
        ebx = (ebx + eax) & MASK
        edx = (edx * eax) & MASK
        ecx = (ecx + edx) & MASK
        edx, ebx = ebx, edx
        i += 2
    ebx = bswap32(ebx)
    return (ebx + ecx) & MASK


def generate_serial(computer_name: str, user_name: str) -> str:
    if not (4 <= len(user_name) <= 32):
        raise ValueError('Name must contain from 4 to 32 characters.')
    data = user_name.encode('ascii', errors='ignore') + bytes(2)
    comp_hash = computer_hash(computer_name)
    ebx = 0
    edx = 0
    ecx = 0x7FFF
    i = 0
    while data[i] != 0:
        bx = data[i] | (data[i + 1] << 8)
        ebx = (ebx & 0xFFFF0000) | bx
        ebx = (ebx << 8) & MASK
        eax = comp_hash & 0x00F8F800
        ebx = (ebx ^ eax) & MASK
        ebx = (ebx + 0x006C6F6C) & MASK
        ebx = (ebx ^ 0x10101010) & MASK
        edx = (edx + ebx) & MASK
        ecx = (ecx + ebx) & MASK
        ecx = (ecx - 0x002D3D2D) & MASK
        ecx = (ecx * 8) & MASK
        ecx = (ecx + eax) & MASK
        i += 1
    edi = esi = 0
    for _ in range(0x10):
        edi = (edi + ecx) & MASK
        esi = (esi + edx) & MASK
        edi = rol(bswap32(edi), 0x10)
        esi = ror(bswap32(esi), 0x10)
    return f'{ecx:08X}-{edx:08X}-{edi:08X}-{esi:08X}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='?', default='TestUser')
    parser.add_argument('--computer', default='LAPCUAPHU')
    args = parser.parse_args()
    print(f'ComputerName: {args.computer}')
    print(f'Name        : {args.name}')
    print(f'Serial      : {generate_serial(args.computer, args.name)}')


if __name__ == '__main__':
    main()
