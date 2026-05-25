#!/usr/bin/env python3
"""
Bai 3 - diablo2oo2 Crackme #09 Python keygen for lab/report use.
"""

from __future__ import annotations
import argparse
import sys

# Bảng ký tự hợp lệ dùng trong quá trình mã hóa
# Gồm:
# - số 0-9
# - chữ thường a-z
# - chữ hoa A-Z
ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def rol8(value: int, bits: int) -> int:
    """
    Hàm rotate left 8-bit.

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


def launch_gui() -> None:
    """
    Giao diện nhập username cho Bài 3.
    """
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title('Bài 3 - Keygen GUI')
    root.resizable(False, False)

    tk.Label(root, text='Username:').grid(row=0, column=0, padx=10, pady=(12, 6), sticky='w')
    name_var = tk.StringVar(value='TestUser')
    name_entry = tk.Entry(root, textvariable=name_var, width=38)
    name_entry.grid(row=0, column=1, padx=10, pady=(12, 6))

    filtered_var = tk.StringVar()
    tk.Label(root, text='Filtered name:').grid(row=1, column=0, padx=10, pady=6, sticky='w')
    filtered_entry = tk.Entry(root, textvariable=filtered_var, width=38, state='readonly')
    filtered_entry.grid(row=1, column=1, padx=10, pady=6)

    serial_var = tk.StringVar()
    tk.Label(root, text='Serial:').grid(row=2, column=0, padx=10, pady=6, sticky='w')
    serial_entry = tk.Entry(root, textvariable=serial_var, width=38, state='readonly')
    serial_entry.grid(row=2, column=1, padx=10, pady=6)

    def generate_clicked() -> None:
        name = name_var.get()
        filtered = sanitize_name(name)
        filtered_var.set(filtered or '(empty)')
        serial = generate_serial(name)
        serial_var.set(serial)
        if serial == 'Invalid Username':
            messagebox.showwarning('Lưu ý', 'Username không có ký tự hợp lệ. Chỉ dùng 0-9, a-z, A-Z.')

    def copy_clicked() -> None:
        serial = serial_var.get()
        if serial and serial != 'Invalid Username':
            root.clipboard_clear()
            root.clipboard_append(serial)
            messagebox.showinfo('Copied', 'Đã copy serial vào clipboard.')

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 12))
    tk.Button(btn_frame, text='Generate', width=14, command=generate_clicked).pack(side='left', padx=5)
    tk.Button(btn_frame, text='Copy Serial', width=14, command=copy_clicked).pack(side='left', padx=5)

    name_entry.focus_set()
    root.mainloop()


def main() -> None:
    """
    Cách chạy:
    - Double-click / không truyền tham số: mở GUI
    - CLI: python bai3_keygen.py TestUser
    - GUI thủ công: python bai3_keygen.py --gui
    """
    parser = argparse.ArgumentParser(description='Bài 3 - diablo2oo2 Crackme #09 keygen')
    parser.add_argument('name', nargs='?', help='Username cần tạo serial')
    parser.add_argument('--gui', action='store_true', help='Mở giao diện nhập username')
    args = parser.parse_args()

    if args.gui or args.name is None:
        launch_gui()
        return

    print(f'Input name   : {args.name}')
    print(f'Filtered name: {sanitize_name(args.name) or "(empty)"}')
    print(f'Serial       : {generate_serial(args.name)}')


if __name__ == '__main__':
    main()
