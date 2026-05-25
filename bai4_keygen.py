#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import sys
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


def launch_gui() -> None:
    """
    Giao diện nhập username cho Bài 4 / WhichKeyIsIt.

    Lưu ý riêng cho Monday:
    - Nếu chọn Thứ 2/Monday, chương trình sẽ tạo thêm file xor0.rox.
    - Hãy để file keygen này cùng thư mục với crackme trước khi Generate,
      để file xor0.rox được sinh đúng trong thư mục crackme.
    """
    import os
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk

    root = tk.Tk()
    root.title('Bài 4 - WhichKeyIsIt Keygen GUI')
    root.resizable(False, False)

    note_text = (
        'NOTE Monday/Thứ 2: Nếu chọn Monday, hãy để file keygen này trong cùng thư mục crackme '
        'trước khi Generate để chương trình sinh file xor0.rox đúng vị trí.'
    )
    note = tk.Label(root, text=note_text, wraplength=430, justify='left', fg='red')
    note.grid(row=0, column=0, columnspan=2, padx=10, pady=(12, 6), sticky='w')

    tk.Label(root, text='Username:').grid(row=1, column=0, padx=10, pady=6, sticky='w')
    name_var = tk.StringVar(value='TestUser')
    name_entry = tk.Entry(root, textvariable=name_var, width=40)
    name_entry.grid(row=1, column=1, padx=10, pady=6)

    tk.Label(root, text='Day:').grid(row=2, column=0, padx=10, pady=6, sticky='w')
    day_var = tk.StringVar(value=current_day())
    day_combo = ttk.Combobox(root, textvariable=day_var, values=DAYS, width=37, state='readonly')
    day_combo.grid(row=2, column=1, padx=10, pady=6)

    tk.Label(root, text='Serial / Result:').grid(row=3, column=0, padx=10, pady=6, sticky='nw')
    result_text = tk.Text(root, width=42, height=7)
    result_text.grid(row=3, column=1, padx=10, pady=6)

    def write_result(text: str) -> None:
        result_text.delete('1.0', 'end')
        result_text.insert('1.0', text)

    def create_monday_file(name: str) -> str:
        b = name.encode('latin-1')
        if len(b) < 4:
            raise ValueError('Monday requires name length >= 4.')
        mul = 0x03 if (b[3] ^ 0x02) == 0x7F else 0x02
        xor_val = 0xFACE2AAD if mul == 0x03 else 0xFACE1850
        file_bytes = [
            0xDE, 0xC0, 0xAD, 0xDE, mul,
            0x74, 0x6F, 0x73, 0x6C, 0x65, 0x65, 0x70, 0x66, 0x6F, 0x72,
            0x65, 0x76, 0x65, 0x72, 0x69, 0x73, 0x6D, 0x79, 0x64, 0x72,
            0x65, 0x61, 0x6D,
            xor_val & 0xFF, (xor_val >> 8) & 0xFF,
            (xor_val >> 16) & 0xFF, (xor_val >> 24) & 0xFF,
        ]
        rox_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xor0.rox')
        with open(rox_path, 'wb') as f:
            f.write(bytes(file_bytes))
        return rox_path

    def generate_clicked() -> None:
        name = name_var.get().strip()
        day = day_var.get().strip().lower()
        try:
            serial = generate(name, day)
            output = f'Username: {name}\nDay     : {day.capitalize()}\nSerial  : {serial}'
            if day == 'monday':
                rox_path = create_monday_file(name)
                output += f'\n\n[Monday] Đã tạo file: {rox_path}'
                output += '\nNhớ đặt file keygen trong thư mục crackme để crackme đọc được file xor0.rox.'
            write_result(output)
        except (RuntimeError, ValueError) as exc:
            write_result(f'Error: {exc}')
            messagebox.showerror('Lỗi', str(exc))

    def generate_all_clicked() -> None:
        name = name_var.get().strip()
        lines = [f'Username: {name}', '']
        for d in DAYS:
            try:
                result = generate(name, d)
            except (RuntimeError, ValueError) as exc:
                result = f'Error: {exc}'
            lines.append(f'{d.capitalize():9}: {result}')
        write_result('\n'.join(lines))

    def copy_clicked() -> None:
        content = result_text.get('1.0', 'end').strip()
        if content:
            root.clipboard_clear()
            root.clipboard_append(content)
            messagebox.showinfo('Copied', 'Đã copy kết quả vào clipboard.')

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=4, column=0, columnspan=2, pady=(8, 12))
    tk.Button(btn_frame, text='Generate', width=14, command=generate_clicked).pack(side='left', padx=5)
    tk.Button(btn_frame, text='Generate All', width=14, command=generate_all_clicked).pack(side='left', padx=5)
    tk.Button(btn_frame, text='Copy Result', width=14, command=copy_clicked).pack(side='left', padx=5)

    name_entry.focus_set()
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description='Keygen for Crackme 4 / WhichKeyIsIt.')
    parser.add_argument('name', nargs='?', help='Username entered in the crackme.')
    parser.add_argument('--day', default=None, help='Day of week (e.g. tuesday). Default: today.')
    parser.add_argument('--all', action='store_true', help='Print serials for all days.')
    parser.add_argument('--gui', action='store_true', help='Mở giao diện nhập username')
    args = parser.parse_args()

    if args.gui or (args.name is None and not args.all):
        launch_gui()
        return

    day = args.day if args.day else current_day()
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
            print('Note: Nếu là Thứ 2/Monday, hãy để file keygen này trong thư mục crackme để file xor0.rox được sinh đúng vị trí.')
        print(f'Username: {name}')
        print(f'Day     : {day.capitalize()}')
        print(f'Serial  : {serial}')


if __name__ == '__main__':
    main()
