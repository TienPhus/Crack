#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
from datetime import datetime

MASK32 = 0xFFFFFFFF
CPUID_EAX0 = (0x00000015, 0x756E6547, 0x6C65746E, 0x49656E69)
CPUID_EAX1 = (0x000606A6, 0x14200800, 0xFEDA3223, 0x1F8BFBFF)


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
    p2 = (p2 ^ (p2 >> 16)) & 0xFFFF
    return f'T10-{p2:04X}'


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
    raise RuntimeError('Saturday branch is not implemented; original uses a larger custom hash path.')


def sunday(name: str | None = None) -> str:
    return 'A10-57617274-686F67'


DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']


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


def current_day() -> str:
    # Match Windows SYSTEMTIME: Sunday=0, Monday=1, ..., Saturday=6
    return DAYS[(datetime.now().weekday() + 1) % 7]


def main() -> None:
    parser = argparse.ArgumentParser(description='Keygen for Crackme 4 / WhichKeyIsIt.')
    parser.add_argument('name', nargs='?', help='Username entered in the crackme.')
    parser.add_argument('--day', default=None, help='Day of week (e.g. tuesday). Default: today.')
    parser.add_argument('--all', action='store_true', help='Print serials for all days.')
    args = parser.parse_args()

    interactive = args.name is None
    day = args.day if args.day else current_day()
    if day.lower() == 'monday' and interactive:
        print('Lưu ý: Hôm nay là Monday — hãy đặt file keygen này cùng thư mục với WhichKeyIsIt.exe trước khi chạy.')
        print()
    name = args.name or input('Username: ').strip()

    if args.all:
        for d in DAYS:
            try:
                result = generate(name, d)
            except (RuntimeError, ValueError) as exc:
                result = f'Error: {exc}'
            print(f'{d.capitalize():9}: {result}')
    else:
        try:
            serial = generate(name, day)
        except (RuntimeError, ValueError) as exc:
            print(f'Error: {exc}')
            if interactive:
                try:
                    input('\nPress Enter to exit...')
                except EOFError:
                    pass
            raise SystemExit(1)
        if day.lower() == 'monday':
            import os
            b = name.encode('latin-1')
            mul = 0x03 if (b[3] ^ 0x02) == 0x7F else 0x02
            xor_val = 0xFACE2AAD if mul == 0x03 else 0xFACE1850
            file_bytes = [0xDE, 0xC0, 0xAD, 0xDE, mul,
                          0x74,0x6F,0x73,0x6C,0x65,0x65,0x70,0x66,0x6F,0x72,
                          0x65,0x76,0x65,0x72,0x69,0x73,0x6D,0x79,0x64,0x72,
                          0x65,0x61,0x6D,
                          xor_val & 0xFF, (xor_val >> 8) & 0xFF,
                          (xor_val >> 16) & 0xFF, (xor_val >> 24) & 0xFF]
            rox_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xor0.rox')
            with open(rox_path, 'wb') as f:
                f.write(bytes(file_bytes))
            print(f'[Monday] Đã tạo: {rox_path}')
        print(f'Username: {name}')
        print(f'Day     : {day.capitalize()}')
        print(f'Serial  : {serial}')

    if interactive:
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass


if __name__ == '__main__':
    main()
