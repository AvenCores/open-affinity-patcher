#!/usr/bin/env python3
"""
PE Resource Extractor & Patcher
Анализ и реализация логики патчера Canva Affinity 3.2.0.4351
Образовательный инструмент для реверс-инжиниринга PE файлов.
"""

import struct
import sys
import os


NULL_BYTE = bytes([0])

class PEStructures:
    IMAGE_DOS_SIGNATURE = b'MZ'
    IMAGE_NT_SIGNATURE = b'PE' + NULL_BYTE + NULL_BYTE
    RT_RCDATA = 10
    
    @staticmethod
    def ror32(value, count):
        count &= 0x1f
        return ((value >> count) | (value << (32 - count))) & 0xFFFFFFFF


class PEDecryptor:
    @staticmethod
    def decrypt(data: bytes, key: int = 0xDEADBEEF) -> bytes:
        """
        Дешифрует данные с использованием алгоритма патчера.
        Алгоритм:
            for i от size downto 1:
                decrypted[i] = encrypted[i] XOR (key & 0xFF)
                key = ROR(key, 1)
                key = key XOR encrypted[i]
                key = key + i
                i--
        """
        result = bytearray(len(data))
        ebx = key
        ecx = len(data)
        
        for i in range(len(data)):
            encrypted_byte = data[i]
            decrypted_byte = encrypted_byte ^ (ebx & 0xFF)
            result[i] = decrypted_byte
            ebx = PEStructures.ror32(ebx, 1)
            ebx ^= encrypted_byte
            ebx = (ebx + ecx) & 0xFFFFFFFF
            ecx -= 1
        
        return bytes(result)


class PELoader:
    def __init__(self, filepath: str = None, data: bytes = None):
        if filepath:
            with open(filepath, 'rb') as f:
                self.data = f.read()
        elif data:
            self.data = data
        else:
            raise ValueError("Укажите filepath или data")
        
        self.sections = []
        self.data_directories = []
        self._parse_headers()
    
    def _parse_headers(self):
        if self.data[:2] != PEStructures.IMAGE_DOS_SIGNATURE:
            raise ValueError("Неверная DOS сигнатура (MZ)")
        
        pe_offset = struct.unpack_from('<I', self.data, 0x3C)[0]
        
        if self.data[pe_offset:pe_offset+4] != PEStructures.IMAGE_NT_SIGNATURE:
            raise ValueError("Неверная PE сигнатура")
        
        self.machine = struct.unpack_from('<H', self.data, pe_offset + 4)[0]
        self.num_sections = struct.unpack_from('<H', self.data, pe_offset + 6)[0]
        self.timestamp = struct.unpack_from('<I', self.data, pe_offset + 8)[0]
        self.opt_header_size = struct.unpack_from('<H', self.data, pe_offset + 20)[0]
        
        opt_header = self.data[pe_offset + 24:pe_offset + 24 + self.opt_header_size]
        self.magic = struct.unpack_from('<H', opt_header, 0)[0]
        self.entry_point = struct.unpack_from('<I', opt_header, 16)[0]
        self.image_base = struct.unpack_from('<I', opt_header, 28)[0] if self.magic == 0x10b else struct.unpack_from('<Q', opt_header, 24)[0]
        
        self.data_directories = []
        for i in range(16):
            rva = struct.unpack_from('<I', opt_header, 96 + i * 8)[0]
            size = struct.unpack_from('<I', opt_header, 96 + i * 8 + 4)[0]
            self.data_directories.append((rva, size))
        
        section_table = pe_offset + 24 + self.opt_header_size
        for i in range(self.num_sections):
            sec_off = section_table + i * 40
            name = self.data[sec_off:sec_off+8].rstrip(NULL_BYTE).decode('ascii', errors='replace')
            vsize = struct.unpack_from('<I', self.data, sec_off + 8)[0]
            vaddr = struct.unpack_from('<I', self.data, sec_off + 12)[0]
            rsize = struct.unpack_from('<I', self.data, sec_off + 16)[0]
            raddr = struct.unpack_from('<I', self.data, sec_off + 20)[0]
            chars = struct.unpack_from('<I', self.data, sec_off + 36)[0]
            self.sections.append({
                'name': name, 'vsize': vsize, 'vaddr': vaddr,
                'rsize': rsize, 'raddr': raddr, 'chars': chars
            })
    
    def rva_to_offset(self, rva: int) -> int:
        for sec in self.sections:
            if sec['vaddr'] <= rva < sec['vaddr'] + max(sec['vsize'], sec['rsize']):
                return rva - sec['vaddr'] + sec['raddr']
        raise ValueError(f"RVA 0x{rva:x} не найден ни в одной секции")
    
    def get_section_by_name(self, name: str) -> dict:
        for sec in self.sections:
            if sec['name'] == name:
                return sec
        return None


class ResourceParser:
    def __init__(self, pe: PELoader):
        self.pe = pe
        self.resources = []
        self.rsrc_raw = 0
        self.rsrc_size = 0
        self.rsrc_vaddr = 0
        self.rsrc_data = b''
        self._parse()
    
    def _parse(self):
        rva, size = self.pe.data_directories[2]
        if rva == 0:
            return
        
        rsrc_sec = self.pe.get_section_by_name('.rsrc')
        if not rsrc_sec:
            return
        
        self.rsrc_raw = rsrc_sec['raddr']
        self.rsrc_size = rsrc_sec['rsize']
        self.rsrc_vaddr = rsrc_sec['vaddr']
        self.rsrc_data = self.pe.data[self.rsrc_raw:self.rsrc_raw + self.rsrc_size]
        
        self._parse_dir(0, [])
    
    def _parse_dir(self, offset: int, path: list):
        if offset + 16 > len(self.rsrc_data):
            return
        
        num_named = struct.unpack_from('<H', self.rsrc_data, offset + 12)[0]
        num_id = struct.unpack_from('<H', self.rsrc_data, offset + 14)[0]
        
        entry_offset = offset + 16
        for i in range(num_named + num_id):
            if entry_offset + 8 > len(self.rsrc_data):
                break
            
            name_id = struct.unpack_from('<I', self.rsrc_data, entry_offset)[0]
            data_offset = struct.unpack_from('<I', self.rsrc_data, entry_offset + 4)[0]
            
            is_data = (data_offset & 0x80000000) == 0
            offset_val = data_offset & 0x7FFFFFFF
            
            if name_id & 0x80000000:
                name_offset = name_id & 0x7FFFFFFF
                name_len = struct.unpack_from('<H', self.rsrc_data, name_offset)[0]
                entry_name = self.rsrc_data[name_offset+2:name_offset+2+name_len*2:2].decode('ascii', errors='replace')
            else:
                entry_name = name_id
            
            current_path = path + [entry_name]
            
            if is_data:
                if offset_val + 16 <= len(self.rsrc_data):
                    data_rva = struct.unpack_from('<I', self.rsrc_data, offset_val)[0]
                    data_size = struct.unpack_from('<I', self.rsrc_data, offset_val + 4)[0]
                    actual_offset = data_rva - self.rsrc_vaddr + self.rsrc_raw
                    
                    self.resources.append({
                        'path': current_path,
                        'rva': data_rva,
                        'size': data_size,
                        'offset': actual_offset
                    })
            else:
                self._parse_dir(offset_val, current_path)
            
            entry_offset += 8
    
    def get_resource_data(self, res: dict) -> bytes:
        off = res['offset']
        size = res['size']
        return self.pe.data[off:off + size]


class PatcherEngine:
    def __init__(self, dll_data: bytes):
        self.dll = PELoader(data=dll_data)
        self.resources = ResourceParser(self.dll)
    
    def extract_patch_info(self) -> list:
        patches = []
        
        for res in self.resources.resources:
            path = res['path']
            if len(path) >= 1 and path[0] == 10:
                data = self.resources.get_resource_data(res)
                
                if len(path) >= 2 and path[1] == 2:
                    files = self._parse_file_list(data)
                    patches.append({'type': 'files', 'files': files})
                
                elif len(path) >= 2 and path[1] == 4:
                    patch_info = self._parse_patch_pattern(data)
                    patches.append({'type': 'pattern', 'info': patch_info})
                
                elif len(path) >= 2 and path[1] == 5:
                    patches.append({'type': 'replace', 'data': data})
        
        return patches
    
    def _parse_file_list(self, data: bytes) -> list:
        files = []
        offset = 0
        
        while offset < len(data):
            if data[offset] == 0:
                offset += 1
                continue
            
            if data[offset] > 0 and data[offset] < 200 and offset + 1 + data[offset] <= len(data):
                name_len = data[offset]
                name = data[offset+1:offset+1+name_len]
                name_clean = name.split(NULL_BYTE)[0]
                if len(name_clean) >= 2 and all(32 <= b < 127 or b in (0x2e, 0x5c) for b in name_clean):
                    files.append(name_clean.decode('ascii'))
                    offset += 1 + name_len
                    continue
            
            end = offset
            while end < len(data) and data[end] != 0:
                end += 1
            if end > offset:
                name = data[offset:end]
                if len(name) >= 2 and all(32 <= b < 127 or b in (0x2e, 0x5c, 0x5f, 0x2d) for b in name):
                    files.append(name.decode('ascii'))
            offset = end + 1
        
        return files
    
    def _parse_patch_pattern(self, data: bytes) -> dict:
        if len(data) < 80:
            return {}
        
        patch_type = struct.unpack_from('<I', data, 0)[0]
        file_offset = struct.unpack_from('<I', data, 0x18)[0]
        
        file_name = ""
        for name_start in range(0x20, min(0x40, len(data))):
            if data[name_start] == 0:
                continue
            end = name_start
            while end < len(data) and data[end] != 0:
                end += 1
            if end > name_start and end - name_start < 100:
                s = data[name_start:end]
                if all(32 <= b < 127 or b in (0x2e, 0x5c, 0x5f, 0x2d) for b in s):
                    file_name = s.decode('ascii')
                    break
        
        replace_size = struct.unpack_from('<I', data, 0x32)[0] if len(data) > 0x36 else 0
        num_patches = struct.unpack_from('<I', data, 0x36)[0] if len(data) > 0x3a else 0
        
        search_start = 0x3a
        search_pattern = data[search_start:search_start + replace_size] if replace_size > 0 else b''
        
        return {
            'type': patch_type,
            'file_offset': file_offset,
            'file_name': file_name,
            'replace_size': replace_size,
            'num_patches': num_patches,
            'search_pattern': search_pattern
        }
    
    def apply_patch(self, target_file: str, search: bytes, replace: bytes, offset: int = None) -> bool:
        if not os.path.exists(target_file):
            print(f"  [!] Файл не найден: {target_file}")
            return False
        
        with open(target_file, 'r+b') as f:
            file_data = bytearray(f.read())
            
            if offset is not None:
                if offset + len(replace) > len(file_data):
                    print(f"  [!] Offset вне диапазона файла")
                    return False
                
                actual = file_data[offset:offset + len(search)]
                if actual != search:
                    print(f"  [!] Паттерн поиска не совпадает на offset 0x{offset:x}")
                    print(f"      Ожидалось: {search.hex()}")
                    print(f"      Найдено:   {actual.hex()}")
                    return False
                
                file_data[offset:offset + len(replace)] = replace
                f.seek(0)
                f.write(file_data)
                f.truncate()
                print(f"  [+] Патч применён: 0x{offset:x} ({len(replace)} bytes)")
                return True
            else:
                pos = file_data.find(search)
                if pos == -1:
                    print(f"  [!] Паттерн не найден в файле")
                    return False
                
                file_data[pos:pos + len(replace)] = replace
                f.seek(0)
                f.write(file_data)
                f.truncate()
                print(f"  [+] Патч применён: 0x{pos:x} ({len(replace)} bytes)")
                return True


def main():
    if len(sys.argv) < 2:
        print("Использование: python patcher.py <patch_file.exe> [target_dir]")
        print("  patch_file.exe  — файл патчера (PE с зашифрованной DLL)")
        print("  target_dir      — директория с файлами для патчинга (опционально)")
        sys.exit(1)
    
    patch_file = sys.argv[1]
    target_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    print("=" * 70)
    print("PE Resource Extractor & Patcher")
    print("Анализ патчера Canva Affinity 3.2.0.4351")
    print("=" * 70)
    
    print(f"\n[1] Загрузка PE файла: {patch_file}")
    try:
        pe = PELoader(patch_file)
    except Exception as e:
        print(f"  [!] Ошибка загрузки: {e}")
        sys.exit(1)
    
    print(f"  [+] Архитектура: {'x64' if pe.machine == 0x8664 else 'x86'}")
    print(f"  [+] Секций: {pe.num_sections}")
    print(f"  [+] Entry point: 0x{pe.entry_point:08x}")
    
    print("\n[2] Парсинг ресурсов...")
    resources = ResourceParser(pe)
    print(f"  [+] Найдено ресурсов: {len(resources.resources)}")
    
    for res in resources.resources:
        path_str = '/'.join(str(p) for p in res['path'])
        print(f"      {path_str}: offset=0x{res['offset']:x}, size={res['size']}")
    
    print("\n[3] Поиск зашифрованной DLL...")
    dll_resource = None
    for res in resources.resources:
        if len(res['path']) >= 2 and res['path'][0] == 10:
            if isinstance(res['path'][1], str) and res['path'][1].upper() == 'DLL':
                dll_resource = res
                break
            elif res['path'][1] == 1 and res['size'] > 60000:
                dll_resource = res
                break
    
    if not dll_resource:
        print("  [!] Зашифрованная DLL не найдена")
        sys.exit(1)
    
    print(f"  [+] DLL найдена: offset=0x{dll_resource['offset']:x}, size={dll_resource['size']}")
    
    print("\n[4] Дешифрование DLL...")
    encrypted_dll = resources.get_resource_data(dll_resource)
    decrypted_dll = PEDecryptor.decrypt(encrypted_dll)
    
    if decrypted_dll[:2] != b'MZ':
        print("  [!] Дешифрование не дало валидный PE")
        sys.exit(1)
    
    print(f"  [+] Дешифрование успешно! ({len(decrypted_dll)} bytes)")
    
    dll_path = "extracted_patcher.dll"
    with open(dll_path, 'wb') as f:
        f.write(decrypted_dll)
    print(f"  [+] DLL сохранена: {dll_path}")
    
    print("\n[5] Анализ патчей в DLL...")
    engine = PatcherEngine(decrypted_dll)
    patches = engine.extract_patch_info()
    
    target_files = []
    search_pattern = None
    replace_data = None
    patch_offset = None
    patch_file_name = None
    
    for p in patches:
        if p['type'] == 'files':
            target_files = p['files']
            print(f"  [+] Файлы для патчинга: {target_files}")
        elif p['type'] == 'pattern':
            info = p['info']
            search_pattern = info.get('search_pattern')
            patch_offset = info.get('file_offset')
            patch_file_name = info.get('file_name', '')
            print(f"  [+] Паттерн поиска: {search_pattern.hex() if search_pattern else 'N/A'}")
            if patch_offset:
                print(f"  [+] Offset: 0x{patch_offset:x}")
            print(f"  [+] Целевой файл: {patch_file_name}")
        elif p['type'] == 'replace':
            replace_data = p['data']
            print(f"  [+] Байты замены: {replace_data.hex()[:64]}...")
    
    print("\n[6] Применение патчей...")
    
    files_to_patch = []
    if target_files:
        files_to_patch.extend(target_files)
    if patch_file_name and patch_file_name not in files_to_patch:
        files_to_patch.append(patch_file_name)
    
    if files_to_patch and search_pattern and replace_data:
        for fname in files_to_patch:
            fpath = os.path.join(target_dir, fname)
            if os.path.exists(fpath):
                print(f"\n  [*] Патчим: {fname}")
                engine.apply_patch(fpath, search_pattern, replace_data[:len(search_pattern)], patch_offset)
            else:
                print(f"\n  [!] Пропуск (не найден): {fname}")
    else:
        print("  [!] Недостаточно данных для применения патчей")
    
    print("\n" + "=" * 70)
    print("Готово!")
    print("=" * 70)


if __name__ == '__main__':
    main()