#!/usr/bin/env python3
"""
Bai 3 - diablo2oo2 Crackme #09 Python keygen for lab/report use.
"""

from __future__ import annotations
import argparse

# Bảng ký tự hợp lệ dùng trong quá trình mã hóa
# Gồm:
# - số 0-9
# - chữ thường a-z
# - chữ hoa A-Z
ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def rol8(value: int, bits: int) -> int:
    """
    Hàm rotate left 8-bit.

    Ví dụ:
        value = 10010110b
        rol8(value, 3)
    sẽ quay vòng các bit sang trái 3 lần.

    &= 0xFF để đảm bảo chỉ giữ lại 8 bit thấp.
    """
    value &= 0xFF
    bits %= 8

    # Quay trái:
    # - value << bits  : dịch trái
    # - value >> (8-bits): phần bị tràn quay lại đầu
    return ((value << bits) | (value >> (8 - bits))) & 0xFF


def sanitize_name(name: str) -> str:
    """
    Lọc username:
    chỉ giữ lại các ký tự nằm trong ALPHABET.

    Ví dụ:
        "Test@123!"
    ->  "Test123"
    """
    return ''.join(ch for ch in name if ch in ALPHABET)


def rotate_table(table: str, offset: int) -> str:
    """
    Xoay bảng ký tự theo offset.

    Ví dụ:
        table = abcdef
        offset = 2

    -> cdefab
    """
    offset %= len(table)
    return table[offset:] + table[:offset]


def encrypt_name(name: str, rotated: str) -> str:
    """
    Hàm mã hóa username.

    Ý tưởng:
    - Khởi tạo dl bằng ký tự đầu tiên sau khi rotate bit.
    - Với mỗi ký tự:
        al = (ký_tự_hiện_tại XOR ký_tự_kế_tiếp) + dl
    - Sau đó cập nhật dl.
    - Dùng al để index vào bảng rotated.

    Đây mô phỏng logic thường thấy trong crackme/keygen ASM.
    """

    # Nếu chuỗi rỗng -> trả về rỗng
    if not name:
        return ''

    # Lấy ký tự đầu tiên rồi rotate trái 3 bit
    dl = rol8(ord(name[0]), 3)

    out = []

    for i, ch in enumerate(name):

        # Ký tự kế tiếp
        # Nếu đang ở cuối chuỗi -> dùng 0
        next_value = ord(name[i + 1]) if i + 1 < len(name) else 0

        # Công thức mã hóa chính
        al = ((ord(ch) ^ next_value) + dl) & 0xFF

        # Cập nhật dl cho vòng lặp tiếp theo
        dl = (dl + al) & 0xFF

        # Chọn ký tự trong bảng rotated
        out.append(rotated[al % len(rotated)])

    return ''.join(out)


def generate_serial(name: str) -> str:
    """
    Sinh serial từ username.
    """

    # Lọc username
    filtered = sanitize_name(name)

    # Nếu sau khi lọc mà rỗng -> invalid
    if not filtered:
        return 'Invalid Username'

    # Offset phụ thuộc độ dài username
    offset = len(filtered) * 4

    # Nếu offset quá lớn thì gán cố định = 0x1E
    if offset > 0x3C:
        offset = 0x1E

    # Tạo bảng ký tự đã rotate
    rotated = rotate_table(ALPHABET, offset)

    # Mã hóa username
    encrypted = encrypt_name(filtered, rotated)

    serial = []

    # Ghép serial dựa trên:
    # - ký tự gốc
    # - ký tự đã mã hóa
    for original_char, encrypted_char in zip(filtered, encrypted):

        # Vị trí của encrypted_char trong bảng rotated
        enc_index = rotated.index(encrypted_char)

        # Rotate lại bảng theo enc_index
        rerotated = rotate_table(rotated, enc_index)

        # Tìm vị trí ký tự gốc
        original_index = rotated.index(original_char)

        # Lấy ký tự serial tương ứng
        serial.append(rerotated[original_index])

    return ''.join(serial)


def main() -> None:
    """
    Hàm main:
    - đọc username từ command line
    - in username đã lọc
    - sinh serial
    """

    parser = argparse.ArgumentParser()

    # Nếu không nhập username
    # -> dùng mặc định "TestUser"
    parser.add_argument('name', nargs='?', default='TestUser')

    args = parser.parse_args()

    print(f'Input name   : {args.name}')
    print(f'Filtered name: {sanitize_name(args.name) or "(empty)"}')
    print(f'Serial       : {generate_serial(args.name)}')


# Điểm bắt đầu chương trình
if __name__ == '__main__':
    main()