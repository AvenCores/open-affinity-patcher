#!/usr/bin/env python3
"""
Canva Affinity Universal Patcher v3
Умный патчер, который сам находит проверку лицензии в libaffinity.dll
Не требует оригинальный патчер.

Логика: ищет функцию с эпилогом "add rsp, 0x20; pop rdi; ret; xor al, al"
и меняет jne на jmp перед вызовом проверки.

Использование:
    python smart_patcher.py libaffinity.dll
    python smart_patcher.py "C:\Program Files\Canva\libaffinity.dll"
"""

import sys
import os
import shutil


def create_backup(filepath: str) -> str:
    backup_path = filepath + ".backup"
    counter = 1
    base_backup = backup_path
    while os.path.exists(backup_path):
        backup_path = f"{base_backup}.{counter}"
        counter += 1
    shutil.copy2(filepath, backup_path)
    print(f"  [+] Бэкап создан: {backup_path}")
    return backup_path


def find_function_epilog(data: bytearray, start: int = 0):
    """Ищет эпилог функции: add rsp, 0x20; pop rdi; ret"""
    epilog = bytes.fromhex("4883c4205fc3")
    pos = start
    while True:
        pos = data.find(epilog, pos)
        if pos == -1:
            break
        yield pos
        pos += 1


def find_jne_before_offset(data: bytearray, offset: int, max_back: int = 80):
    """Ищет jne (75 xx) в пределах max_back байт до offset."""
    start = max(0, offset - max_back)
    for i in range(start, offset - 1):
        if data[i] == 0x75:
            # Следующий байт = relative offset
            rel = data[i + 1]
            jump_target = i + 2 + rel if rel < 0x80 else i + 2 - (0x100 - rel)
            # Проверяем, что jne прыгает вперёд (внутри функции)
            if i + 2 <= jump_target <= offset:
                return i
    return -1


def has_call_instruction(data: bytearray, start: int, end: int):
    """Проверяет наличие call в диапазоне [start, end]."""
    for i in range(start, end - 1):
        # call [rax] = ff 10
        # call [rip+...] = ff 15
        # call rel32 = e8 xx xx xx xx
        if data[i] == 0xff and data[i+1] in (0x10, 0x15):
            return True
        if data[i] == 0xe8 and i + 5 <= end:
            return True
    return False


def find_license_checks(data: bytearray):
    """Находит все потенциальные проверки лицензии в файле."""
    checks = []

    # Способ 1: ищем полный оригинальный паттерн из dUP2
    original_pattern = bytes.fromhex("750f48000000ba0100000048000000ff10400fb6c7488b5c24384883c4205fc332c0")
    pos = data.find(original_pattern)
    if pos != -1:
        checks.append({
            'offset': pos,
            'type': 'original_pattern',
            'confidence': 100,
            'context': data[max(0, pos-10):pos+50]
        })
        return checks

    # Способ 2: ищем эпилог функции с xor al, al после ret
    epilog_with_xor = bytes.fromhex("4883c4205fc332c0")
    pos = 0
    while True:
        pos = data.find(epilog_with_xor, pos)
        if pos == -1:
            break
        # Идём назад и ищем jne
        jne_pos = find_jne_before_offset(data, pos, 100)
        if jne_pos != -1:
            # Проверяем, что между jne и эпилогом есть call
            if has_call_instruction(data, jne_pos, pos):
                checks.append({
                    'offset': jne_pos,
                    'type': 'epilog_xor',
                    'confidence': 90,
                    'context': data[max(0, jne_pos-10):pos+10]
                })
        pos += 1

    # Способ 3: ищем эпилог без xor, но с int3 padding
    epilog_basic = bytes.fromhex("4883c4205fc3")
    pos = 0
    while True:
        pos = data.find(epilog_basic, pos)
        if pos == -1:
            break
        # Проверяем, что после ret идёт int3 (cc) или nop (90) — признак конца функции
        after_ret = pos + 6
        if after_ret < len(data) and data[after_ret] in (0xcc, 0x90):
            jne_pos = find_jne_before_offset(data, pos, 100)
            if jne_pos != -1:
                if has_call_instruction(data, jne_pos, pos):
                    # Проверяем, что это ещё не добавлено
                    already_found = any(c['offset'] == jne_pos for c in checks)
                    if not already_found:
                        checks.append({
                            'offset': jne_pos,
                            'type': 'epilog_basic',
                            'confidence': 70,
                            'context': data[max(0, jne_pos-10):pos+10]
                        })
        pos += 1

    # Способ 4: ищем movzx eax, dil (40 0f b6 c7) — редкая инструкция, характерная для проверки
    movzx_pattern = bytes.fromhex("400fb6c7")
    pos = 0
    while True:
        pos = data.find(movzx_pattern, pos)
        if pos == -1:
            break
        # Идём назад и ищем jne и call
        jne_pos = find_jne_before_offset(data, pos, 80)
        if jne_pos != -1:
            if has_call_instruction(data, jne_pos, pos):
                already_found = any(c['offset'] == jne_pos for c in checks)
                if not already_found:
                    checks.append({
                        'offset': jne_pos,
                        'type': 'movzx',
                        'confidence': 85,
                        'context': data[max(0, jne_pos-10):pos+20]
                    })
        pos += 1

    return checks


def apply_patch_at(data: bytearray, offset: int) -> bool:
    """Применяет патч: меняет jne (75) на jmp (eb)."""
    if data[offset] != 0x75:
        print(f"  [!] На offset 0x{offset:x} не jne (ожидалось 75, найдено {data[offset]:02x})")
        return False

    old_byte = data[offset]
    data[offset] = 0xeb  # jmp
    print(f"  [+] Патч применён: 0x{offset:x}: {old_byte:02x} (jne) → eb (jmp)")
    return True


def main():
    print("=" * 70)
    print("Canva Affinity Universal Patcher v3")
    print("Умный поиск и патчинг проверки лицензии")
    print("=" * 70)

    if len(sys.argv) < 2:
        target = "libaffinity.dll"
        if not os.path.exists(target):
            print(f"\n[!] Укажите путь к libaffinity.dll")
            print(f"    Использование: python {sys.argv[0]} <путь_к_dll>")
            sys.exit(1)
    else:
        target = sys.argv[1]

    if not os.path.exists(target):
        print(f"\n[!] Файл не найден: {target}")
        sys.exit(1)

    with open(target, 'rb') as f:
        data = bytearray(f.read())

    print(f"\n[*] Анализ: {target}")
    print(f"  [+] Размер: {len(data)} bytes")

    # Проверяем PE
    if data[:2] != b'MZ':
        print(f"  [!] Не PE файл")
        sys.exit(1)

    print(f"\n[*] Поиск проверок лицензии...")
    checks = find_license_checks(data)

    if not checks:
        print(f"\n  [!] Проверки лицензии не найдены.")
        print(f"      Возможные причины:")
        print(f"      • Файл уже пропатчен")
        print(f"      • Неверная версия libaffinity.dll")
        print(f"      • Файл сильно отличается от ожидаемого")
        sys.exit(1)

    print(f"\n  [+] Найдено потенциальных проверок: {len(checks)}")

    # Сортируем по уверенности
    checks.sort(key=lambda x: x['confidence'], reverse=True)

    for i, check in enumerate(checks):
        print(f"\n  [{i+1}] Offset: 0x{check['offset']:x}")
        print(f"      Тип: {check['type']}")
        print(f"      Уверенность: {check['confidence']}%")
        print(f"      Контекст: {check['context'].hex()}")

    # Если только одна высокоуверенная проверка — патчим автоматически
    high_confidence = [c for c in checks if c['confidence'] >= 80]

    if len(high_confidence) == 1:
        check = high_confidence[0]
        print(f"\n[*] Автоматический патч (уверенность {check['confidence']}%)")
        create_backup(target)
        if apply_patch_at(data, check['offset']):
            with open(target, 'wb') as f:
                f.write(data)
            print(f"\n[+] Успешно пропатчено!")
        else:
            print(f"\n[!] Ошибка применения патча")
    elif len(high_confidence) > 1:
        print(f"\n[!] Найдено несколько высокоуверенных проверок ({len(high_confidence)}).")
        print(f"    Пожалуйста, выберите вручную:")
        for i, check in enumerate(high_confidence):
            print(f"      {i+1}. Offset 0x{check['offset']:x} ({check['type']}, {check['confidence']}%)")

        try:
            choice = int(input(f"\n    Введите номер (1-{len(high_confidence)}): ")) - 1
            if 0 <= choice < len(high_confidence):
                check = high_confidence[choice]
                create_backup(target)
                if apply_patch_at(data, check['offset']):
                    with open(target, 'wb') as f:
                        f.write(data)
                    print(f"\n[+] Успешно пропатчено!")
            else:
                print(f"\n[!] Неверный выбор")
        except (ValueError, EOFError):
            print(f"\n[!] Отменено пользователем")
    else:
        print(f"\n[!] Нет высокоуверенных проверок. Найдено {len(checks)} с низкой уверенностью.")
        print(f"    Это может быть рискованно. Показать все? (y/n)")
        try:
            answer = input("    > ").lower()
            if answer == 'y':
                for i, check in enumerate(checks):
                    print(f"      {i+1}. Offset 0x{check['offset']:x} ({check['type']}, {check['confidence']}%)")
                choice = int(input(f"\n    Введите номер (1-{len(checks)}): ")) - 1
                if 0 <= choice < len(checks):
                    check = checks[choice]
                    create_backup(target)
                    if apply_patch_at(data, check['offset']):
                        with open(target, 'wb') as f:
                            f.write(data)
                        print(f"\n[+] Успешно пропатчено!")
        except (ValueError, EOFError):
            print(f"\n[!] Отменено")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()