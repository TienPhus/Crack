#!/usr/bin/env python3
"""
Bai 2 - errors_keygenme Python keygen for lab/report use.
"""

from __future__ import annotations
import argparse

# Mask 32-bit:
# dùng để đảm bảo mọi phép toán luôn nằm trong phạm vi 32 bit
MASK32 = 0xFFFFFFFF


def u32(x: int) -> int:
    """
    Ép giá trị về unsigned 32-bit.

    Trong ASM/C:
    các thanh ghi 32-bit sẽ tự overflow.
    Python thì integer không giới hạn,
    nên cần mask lại bằng 0xFFFFFFFF.
    """
    return x & MASK32


def rol32(x: int, n: int) -> int:
    """
    Rotate Left 32-bit.

    Quay trái n bit:
    - phần tràn bên trái quay về bên phải.
    """

    # Đảm bảo n nằm trong khoảng 0..31
    n &= 31

    # Giữ 32 bit thấp
    x &= MASK32

    return ((x << n) | (x >> (32 - n))) & MASK32


def ror32(x: int, n: int) -> int:
    """
    Rotate Right 32-bit.

    Quay phải n bit:
    - phần tràn bên phải quay về bên trái.
    """

    n &= 31
    x &= MASK32

    return ((x >> n) | (x << (32 - n))) & MASK32


def bswap32(x: int) -> int:
    """
    Byte Swap 32-bit.

    Đảo thứ tự các byte trong 1 DWORD.

    Ví dụ:
        0x12345678
    ->  0x78563412

    Tương đương lệnh BSWAP trong x86.
    """

    x &= MASK32

    return (
        ((x & 0x000000FF) << 24) |
        ((x & 0x0000FF00) << 8) |
        ((x & 0x00FF0000) >> 8) |
        ((x & 0xFF000000) >> 24)
    )


def build_schedule(name: str) -> list[int]:
    """
    Tạo message schedule giống SHA-1.

    Các bước:
    1. Encode username thành bytes
    2. Padding dữ liệu
    3. Chia thành các word 32-bit
    4. Mở rộng thành 96 word
    """

    # Encode chuỗi sang latin-1
    raw = name.encode('latin-1')

    # Giới hạn độ dài
    # vì implementation này chỉ xử lý 1 block 512-bit
    if len(raw) > 55:
        raise ValueError('This crackme implementation expects <= 55 bytes.')

    # Tạo buffer 64 byte (512 bit)
    buf = bytearray(64)

    # Copy dữ liệu username vào đầu buffer
    buf[:len(raw)] = raw

    # Padding kiểu SHA:
    # thêm bit 1 (0x80)
    buf[len(raw)] = 0x80

    # Byte cuối chứa độ dài dữ liệu (bit length)
    # len(raw) << 3 = số bit
    buf[63] = (len(raw) << 3) & 0xFF

    words = []

    # Chia buffer thành 16 word 32-bit
    for i in range(16):

        # Đọc 4 byte little-endian
        # rồi đảo byte thành big-endian
        words.append(
            bswap32(
                int.from_bytes(
                    buf[i * 4:(i + 1) * 4],
                    'little'
                )
            )
        )

    # Mở rộng message schedule:
    # W[i] = rol1(W[i-3] XOR W[i-8] XOR W[i-14] XOR W[i-16])
    for i in range(16, 96):

        words.append(
            rol32(
                words[i - 3] ^
                words[i - 8] ^
                words[i - 14] ^
                words[i - 16],
                1
            )
        )

    return words


def generate_key(name: str) -> str:
    """
    Sinh serial từ username.

    Thuật toán gần giống SHA-1:
    - dùng 5 thanh ghi a,b,c,d,e
    - chạy 80 round
    - dùng rotate/XOR/AND/OR
    """

    # Tạo message schedule
    w = build_schedule(name)

    # Initial hash constants (SHA-1 IV)
    h = [
        0x67452301,
        0xEFCDAB89,
        0x98BADCFE,
        0x10325476,
        0xC3D2E1F0
    ]

    # Copy vào các thanh ghi làm việc
    a, b, c, d, e = h

    # 80 vòng xử lý chính
    for i in range(80):

        # Chọn hàm logic + constant theo từng phase
        if i < 20:

            # Chức năng chọn bit
            f = (b & c) | ((~b) & d)

            # Hằng số phase 1
            k = 0x5A827999

        elif i < 40:

            # XOR logic
            f = b ^ c ^ d

            # Hằng số phase 2
            k = 0x6ED9EBA1

        elif i < 60:

            # Majority function
            f = (b & c) | (b & d) | (c & d)

            # Hằng số phase 3
            k = 0x8F1BBCDC

        else:

            # XOR logic
            f = b ^ c ^ d

            # Hằng số phase 4
            k = 0x0CA62C1D6

        # Công thức chính
        temp = u32(
            rol32(a, 5) +
            f +
            e +
            k +
            w[i]
        )

        # Dịch thanh ghi
        e = d
        d = c

        # SHA-1 dùng rol30(b)
        # ở đây dùng ror2(b) tương đương
        c = ror32(b, 2)

        b = a
        a = temp

    # Cộng kết quả với initial hash
    result = [
        u32(x + y)
        for x, y in zip(h, [a, b, c, d, e])
    ]

    out = []

    # Chuyển hash thành serial dạng ký tự
    for word in result:

        # Chuyển DWORD thành 4 byte little-endian
        for byte in word.to_bytes(4, 'little'):

            # Chỉ lấy nibble thấp (4 bit thấp)
            n = byte & 0x0F

            # 0-9 -> '0'..'9'
            if n <= 9:
                out.append(chr(n + ord('0')))

            # 10-15 -> 'A'..'F'
            else:
                out.append(chr(n - 1 + ord('A')))

    return ''.join(out)


def main() -> None:
    """
    Hàm main:
    - đọc username từ command line
    - sinh serial
    """

    parser = argparse.ArgumentParser()

    # Nếu không nhập username
    # -> dùng mặc định "TestUser"
    parser.add_argument('name', nargs='?', default='TestUser')

    args = parser.parse_args()

    print(f'Name  : {args.name}')
    print(f'Serial: {generate_key(args.name)}')


# Điểm bắt đầu chương trình
if __name__ == '__main__':
    main()