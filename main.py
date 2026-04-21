#!/usr/bin/env python3
"""
Canva Affinity 3.2.0.4351 Standalone Patcher
Автономный патчер для libaffinity.dll
Не требует оригинального патчера — все данные встроены в скрипт.

Использование:
    python patcher.py libaffinity.dll
    python patcher.py "C:\Program Files\Canva\libaffinity.dll"
    python patcher.py                          # ищет libaffinity.dll рядом

Создаёт бэкап: libaffinity.dll.backup
"""

import sys
import os
import shutil


# ═══════════════════════════════════════════════════════════════════════════════
# ВСТРОЕННЫЕ ДАННЫЕ ПАТЧА (извлечены из dUP2 патчера Canva Affinity 3.2.0.4351)
# ═══════════════════════════════════════════════════════════════════════════════

# Паттерн поиска (34 bytes) — оригинальный код проверки лицензии в libaffinity.dll
# Это x64 код, который вызывает функцию проверки лицензии.
# Если условие jne не срабатывает — выполняется call [rax] (проверка лицензии).
SEARCH_PATTERN = bytes.fromhex(
    "750f"              # jne     +15          ; прыжок если НЕ равно
    "48000000"          # add     [rax], al    ; padding
    "ba01000000"        # mov     edx, 1       ; аргумент
    "48000000"          # add     [rax], al    ; padding
    "ff10"              # call    [rax]        ; ← ВЫЗОВ ПРОВЕРКИ ЛИЦЕНЗИИ
    "400fb6c7"          # movzx   eax, dil     ; получение результата
    "488b5c2438"        # mov     rbx, [rsp+0x38]
    "4883c420"          # add     rsp, 0x20
    "5f"                # pop     rdi
    "c3"                # ret
    "32c0"              # xor     al, al       ; return false
)

# Паттерн замены (34 bytes) — код, который заменяет проверку лицензии.
# После замены функция проверки всегда возвращает успех.
REPLACE_PATTERN = bytes.fromhex(
    "0adeedfa"          # or      bl, dh
    "00ccddf7"          # add     ah, cl
    "00175588"          # add     [rdi+rdx*4-0x78], dl
    "00ccddf7"          # add     ah, cl
    "00175588"          # add     [rdi+rdx*4-0x78], dl
    "00ccddf7"          # add     ah, cl
    "00175588"          # add     [rdi+rdx*4-0x78], dl
    "00ccddf7"          # add     ah, cl
    "00175588"          # add     [rdi+rdx*4-0x78], dl
    "00"                # add     [rax], al
)

# Offset в файле libaffinity.dll, где находится паттерн (RVA 0x100831)
PATCH_OFFSET = 0x100831

# Имя целевого файла
TARGET_FILENAME = "libaffinity.dll"

# ═══════════════════════════════════════════════════════════════════════════════
# ЛОГИКА ПАТЧЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def create_backup(filepath: str) -> str:
    """Создаёт бэкап файла."""
    backup_path = filepath + ".backup"
    counter = 1

    # Если бэкап уже есть — создаём с номером
    base_backup = backup_path
    while os.path.exists(backup_path):
        backup_path = f"{base_backup}.{counter}"
        counter += 1

    shutil.copy2(filepath, backup_path)
    print(f"  [+] Бэкап создан: {backup_path}")
    return backup_path


def verify_pattern(file_data: bytearray, offset: int, pattern: bytes) -> bool:
    """Проверяет, совпадает ли паттерн по указанному offset."""
    if offset + len(pattern) > len(file_data):
        print(f"  [!] Offset 0x{offset:x} вне диапазона файла (размер: {len(file_data)})")
        return False

    actual = file_data[offset:offset + len(pattern)]
    if actual != pattern:
        print(f"  [!] Паттерн НЕ совпадает на offset 0x{offset:x}")
        print(f"      Ожидалось: {pattern.hex()}")
        print(f"      Найдено:   {actual.hex()}")
        return False

    print(f"  [+] Паттерн подтверждён на offset 0x{offset:x}")
    return True


def apply_patch(filepath: str) -> bool:
    """Применяет патч к файлу."""
    print(f"\n[*] Обработка: {filepath}")

    # Читаем файл
    with open(filepath, 'rb') as f:
        file_data = bytearray(f.read())

    print(f"  [+] Размер файла: {len(file_data)} bytes")

    # Проверяем паттерн по известному offset
    if verify_pattern(file_data, PATCH_OFFSET, SEARCH_PATTERN):
        offset = PATCH_OFFSET
    else:
        # Пробуем найти паттерн по всему файлу
        print(f"  [i] Поиск паттерна по всему файлу...")
        pos = file_data.find(SEARCH_PATTERN)
        if pos == -1:
            print(f"  [!] Паттерн не найден. Возможные причины:")
            print(f"      • Файл уже пропатчен")
            print(f"      • Неверная версия libaffinity.dll (ожидается 3.2.0.4351)")
            print(f"      • Файл повреждён или модифицирован")
            return False
        print(f"  [+] Паттерн найден на offset 0x{pos:x}")
        offset = pos

    # Создаём бэкап
    create_backup(filepath)

    # Применяем замену
    file_data[offset:offset + len(REPLACE_PATTERN)] = REPLACE_PATTERN

    # Записываем изменения
    with open(filepath, 'wb') as f:
        f.write(file_data)

    print(f"  [+] Патч успешно применён!")
    print(f"      Offset: 0x{offset:x}")
    print(f"      Заменено: {len(REPLACE_PATTERN)} bytes")
    print(f"      Оригинал: {SEARCH_PATTERN.hex()}")
    print(f"      Замена:   {REPLACE_PATTERN.hex()}")
    return True


def main():
    print("=" * 70)
    print("Canva Affinity 3.2.0.4351 Standalone Patcher")
    print("Автономный патчер для libaffinity.dll")
    print("=" * 70)

    # Определяем целевой файл
    if len(sys.argv) >= 2:
        target = sys.argv[1]
    else:
        target = TARGET_FILENAME
        if not os.path.exists(target):
            print(f"\n[!] Файл {TARGET_FILENAME} не найден в текущей директории.")
            print(f"    Использование: python {sys.argv[0]} <путь_к_libaffinity.dll>")
            sys.exit(1)

    # Проверяем существование файла
    if not os.path.exists(target):
        print(f"\n[!] Файл не найден: {target}")
        sys.exit(1)

    # Проверяем, что это PE файл
    with open(target, 'rb') as f:
        sig = f.read(2)

    if sig != b'MZ':
        print(f"\n[!] Файл не является PE (DOS сигнатура: {sig})")
        sys.exit(1)

    # Применяем патч
    success = apply_patch(target)

    print("\n" + "=" * 70)
    if success:
        print("[+] Патчинг завершён успешно!")
        print("[=] Оригинальный файл сохранён с расширением .backup")
    else:
        print("[!] Патчинг не удался.")
    print("=" * 70)


if __name__ == '__main__':
    main()