#!/usr/bin/env python3
"""
Bai 1 - KeygenMe1 Python keygen.
"""
from __future__ import annotations
import argparse
import socket

# Mask 32-bit:
# dùng để đảm bảo mọi phép toán luôn nằm trong phạm vi 32 bit
MASK32 = 0xFFFFFFFF


def ror8(value: int, bits: int) -> int:
    """
    Rotate Right 8-bit.

    Quay phải bits bit trên 1 byte:
    - phần tràn bên phải quay về bên trái.

    Tương đương lệnh: ror al, 4
    """

    # Giữ 8 bit thấp
    value &= 0xFF

    # Đảm bảo bits nằm trong khoảng 0..7
    bits %= 8

    return ((value >> bits) | (value << (8 - bits))) & 0xFF


def rol32(value: int, bits: int) -> int:
    """
    Rotate Left 32-bit.

    Quay trái bits bit:
    - phần tràn bên trái quay về bên phải.

    Tương đương lệnh: rol edi, 10h
    """

    # Giữ 32 bit thấp
    value &= MASK32

    # Đảm bảo bits nằm trong khoảng 0..31
    bits %= 32

    return ((value << bits) | (value >> (32 - bits))) & MASK32


def ror32(value: int, bits: int) -> int:
    """
    Rotate Right 32-bit.

    Quay phải bits bit:
    - phần tràn bên phải quay về bên trái.

    Tương đương lệnh: ror esi, 10h
    """

    value &= MASK32
    bits %= 32

    return ((value >> bits) | (value << (32 - bits))) & MASK32


def bswap32(value: int) -> int:
    """
    Byte Swap 32-bit.

    Đảo thứ tự các byte trong 1 DWORD.

    Ví dụ:
        0x12345678
    ->  0x78563412

    Tương đương lệnh: bswap ebx / bswap edi / bswap esi
    """

    value &= MASK32

    return (
        ((value & 0x000000FF) << 24) |
        ((value & 0x0000FF00) <<  8) |
        ((value & 0x00FF0000) >>  8) |
        ((value & 0xFF000000) >> 24)
    )


def computer_hash(computer_name: str) -> int:
    """
    Tính hash từ tên máy tính.

    Dịch từ hàm ComputerName proc trong ASM:
        invoke GetComputerName, addr szComputerName, addr nSize
        MOV esi, offset szComputerName
        xor eax,eax / xor edx,edx / xor ebx,ebx / xor ecx,ecx
        .while word ptr ds:[esi]
            mov al,  byte ptr ds:[esi]
            mov dl,  byte ptr ds:[esi+1]
            ror al,  4
            not dl
            add al,  dl
            add ebx, eax
            imul edx,eax
            add ecx, edx
            xchg edx,ebx
            add esi, 2
        .endw
        bswap ebx
        add ebx, ecx
        mov dwCompuHash, ebx

    Lưu ý quan trọng:
        Các lệnh mov al / mov dl chỉ thay byte thấp,
        3 byte cao của EAX / EDX được GIỮ NGUYÊN từ vòng trước.
        Đây là đặc điểm x86 partial register write.
    """

    # Encode tên máy thành bytes ASCII
    # thêm 2 byte null để vòng lặp kết thúc an toàn
    data = computer_name.encode('ascii', errors='ignore') + b'\x00\x00'

    # Khởi tạo các thanh ghi
    # xor eax,eax / xor edx,edx / xor ebx,ebx / xor ecx,ecx
    eax = edx = ebx = ecx = 0

    i = 0

    # .while word ptr ds:[esi]
    # lặp khi 2 byte tại vị trí i khác 0
    while i + 1 < len(data) and (data[i] | (data[i + 1] << 8)) != 0:

        # mov al, byte ptr ds:[esi]
        # chỉ thay byte thấp AL, giữ nguyên 3 byte cao của EAX
        eax = (eax & 0xFFFFFF00) | data[i]

        # mov dl, byte ptr ds:[esi+1]
        # chỉ thay byte thấp DL, giữ nguyên 3 byte cao của EDX
        edx = (edx & 0xFFFFFF00) | data[i + 1]

        # ror al, 4
        # xoay phải byte thấp AL 4 bit, 3 byte cao không đổi
        al = ror8(eax & 0xFF, 4)
        eax = (eax & 0xFFFFFF00) | al

        # not dl
        # đảo bit byte thấp DL
        dl = (~(edx & 0xFF)) & 0xFF
        edx = (edx & 0xFFFFFF00) | dl

        # add al, dl
        # chỉ AL thay đổi, 3 byte cao EAX không đổi
        al = (al + dl) & 0xFF
        eax = (eax & 0xFFFFFF00) | al

        # add ebx, eax  (EAX đầy đủ 32-bit tham gia)
        ebx = (ebx + eax) & MASK32

        # imul edx, eax  (EDX đầy đủ 32-bit tham gia)
        edx = (edx * eax) & MASK32

        # add ecx, edx
        ecx = (ecx + edx) & MASK32

        # xchg edx, ebx
        edx, ebx = ebx, edx

        # add esi, 2
        i += 2

    # bswap ebx
    ebx = bswap32(ebx)

    # add ebx, ecx  →  kết quả là dwCompuHash
    return (ebx + ecx) & MASK32


def generate_serial(computer_name: str, user_name: str) -> str:
    """
    Sinh serial từ tên máy và username.

    Dịch từ hàm CalculateSerialPart1 proc trong ASM.
    Serial gồm 3 giai đoạn tính toán:
        Giai đoạn 1 – tính comp_hash từ tên máy
        Giai đoạn 2 – vòng lặp qua từng ký tự username
        Giai đoạn 3 – 16 vòng hoàn thiện edi, esi

    Output format: "%08X-%08X-%08X-%08X"  (ecx, edx, edi, esi)
    """

    # Kiểm tra độ dài tên (giống check trong WndProc)
    if len(user_name) < 4:
        raise ValueError('Need at least 4 characters.')
    if len(user_name) > 30:
        raise ValueError('Name too long (max 30).')

    # ── Giai đoạn 1: tính computer hash ──────────────────────────────────────
    # invoke ComputerName  →  dwCompuHash
    comp_hash = computer_hash(computer_name)

    # ── Giai đoạn 2: vòng lặp qua từng ký tự username ────────────────────────
    # Encode username thành bytes
    # thêm 2 byte null để đọc word an toàn ở ký tự cuối
    name_bytes = user_name.encode('ascii', errors='ignore') + b'\x00\x00'

    # Khởi tạo thanh ghi
    # xor ebx,ebx / xor edx,edx / mov ecx,07fffh
    ebx = 0
    edx = 0
    ecx = 0x7FFF

    i = 0

    # .while BYTE PTR DS:[esi]
    # lặp cho đến khi gặp byte null
    while name_bytes[i] != 0:

        # mov bx, word ptr ds:[esi]
        # lấy 2 byte liên tiếp dạng little-endian
        # chỉ set 16 bit thấp của EBX, 16 bit cao giữ nguyên
        bx = name_bytes[i] | (name_bytes[i + 1] << 8)
        ebx = (ebx & 0xFFFF0000) | bx

        # shl ebx, 8
        ebx = (ebx << 8) & MASK32

        # mov eax, dwCompuHash  +  and eax, 0f8f800h
        # lấy phần mask từ computer hash
        eax = comp_hash & 0x00F8F800

        # xor ebx, eax
        ebx = (ebx ^ eax) & MASK32

        # add ebx, 06c6f6ch
        ebx = (ebx + 0x006C6F6C) & MASK32

        # xor ebx, 010101010h
        ebx = (ebx ^ 0x10101010) & MASK32

        # add edx, ebx
        edx = (edx + ebx) & MASK32

        # add ecx, ebx
        ecx = (ecx + ebx) & MASK32

        # sub ecx, 02d3d2dh
        ecx = (ecx - 0x002D3D2D) & MASK32

        # imul ecx, ecx, 8
        ecx = (ecx * 8) & MASK32

        # add ecx, eax
        ecx = (ecx + eax) & MASK32

        # inc esi
        i += 1

    # ── Giai đoạn 3: 16 vòng hoàn thiện edi, esi ─────────────────────────────
    # xor edi,edi / xor esi,esi
    edi = 0
    esi = 0

    # mov eax, 010h  →  16 vòng lặp
    for _ in range(0x10):

        # add edi, ecx
        edi = (edi + ecx) & MASK32

        # add esi, edx
        esi = (esi + edx) & MASK32

        # bswap edi
        edi = bswap32(edi)

        # bswap esi
        esi = bswap32(esi)

        # rol edi, 010h
        edi = rol32(edi, 0x10)

        # ror esi, 010h
        esi = ror32(esi, 0x10)

    # wsprintf format: "%08X-%08X-%08X-%08X"
    return f'{ecx:08X}-{edx:08X}-{edi:08X}-{esi:08X}'


def main() -> None:
    """
    Hàm main:
    - đọc username từ command line (mặc định: TestUser)
    - tự lấy tên máy từ hệ điều hành và uppercase
    - sinh serial
    """

    parser = argparse.ArgumentParser(
        description='KeygenMe1 – keygen dịch từ ASM gốc của cosmos/qwertydid'
    )

    # Nếu không nhập username
    # -> dùng mặc định "TestUser"
    parser.add_argument(
        'name', nargs='?', default='TestUser',
        help='Username cần tạo serial (4–30 ký tự ASCII)'
    )

    # Nếu không nhập --computer
    # -> tự lấy hostname của máy và uppercase
    parser.add_argument(
        '--computer', default=None,
        help='Tên máy tính (mặc định: tự lấy từ hệ điều hành, tự uppercase)'
    )

    args = parser.parse_args()

    # Tự lấy hostname và uppercase
    # khớp với GetComputerName trên Windows
    computer = (args.computer or socket.gethostname()).upper()

    print(f'ComputerName : {computer}')
    print(f'Name         : {args.name}')

    try:
        serial = generate_serial(computer, args.name)
        print(f'Serial       : {serial}')
    except ValueError as e:
        print(f'Lỗi: {e}')


# Điểm bắt đầu chương trình
if __name__ == '__main__':
    main()