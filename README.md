<div align="center">
    <a href="https://www.youtube.com/@avencores/" target="_blank">
      <img src="https://github.com/user-attachments/assets/338bcd74-e3c3-4700-87ab-7985058bd17e" alt="YouTube" height="40">
    </a>
    <a href="https://t.me/avencoresyt" target="_blank">
      <img src="https://github.com/user-attachments/assets/939f8beb-a49a-48cf-89b9-d610ee5c4b26" alt="Telegram" height="40">
    </a>
    <a href="https://vk.ru/avencoresreuploads" target="_blank">
      <img src="https://github.com/user-attachments/assets/dc109dda-9045-4a06-95a5-3399f0e21dc4" alt="VK" height="40">
    </a>
    <a href="https://dzen.ru/avencores" target="_blank">
      <img src="https://github.com/user-attachments/assets/bd55f5cf-963c-4eb8-9029-7b80c8c11411" alt="Dzen" height="40">
    </a>
</div>

# 🔧 Open Affinity Patcher
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/AvenCores/open-affinity-patcher)
[![GPL-3.0 License](https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/AvenCores/open-affinity-patcher?style=for-the-badge)](https://github.com/AvenCores/open-affinity-patcher/stargazers)
![GitHub forks](https://img.shields.io/github/forks/AvenCores/open-affinity-patcher?style=for-the-badge)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/AvenCores/open-affinity-patcher?style=for-the-badge)](https://github.com/AvenCores/open-affinity-patcher/pulls)
[![GitHub issues](https://img.shields.io/github/issues/AvenCores/open-affinity-patcher?style=for-the-badge)](https://github.com/AvenCores/open-affinity-patcher/issues)

Интерактивный патчер `libaffinity.dll` для Windows для отключения принудительной авторизации и офлайн работы в Affinity.

Утилита патчит `libaffinity.dll` по смещению `0x0043E451` и заменяет:

- `32 C0` -> `B0 01`
- `XOR AL, AL` -> `MOV AL, 1`
- Эффект: пропатченная функция возвращает `1` вместо `0`

<img alt="file" src="https://github.com/user-attachments/assets/545870d2-8947-4c96-847f-a9836608a0d9" />

## ✨ Что делает патчер

- Работает в интерактивном режиме меню и в режиме прямого запуска через CLI
- Использует путь по умолчанию `C:\Program Files\Affinity\Affinity\libaffinity.dll`
- Позволяет выбрать свой путь к DLL или папку, содержащую `libaffinity.dll`
- Создает резервную копию `.bak` перед изменением файла
- Определяет, был ли файл уже запатчен
- Отказывается применять патч, если байты по целевому смещению отличаются от ожидаемых
- Показывает текущий статус патча в главном меню

## 📋 Проверка поддерживаемой версии

Программа читает установленную версию Affinity из:

`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{D5B4183A-DE48-405A-A106-D3E48EBFE23F}\DisplayVersion`

Ожидаемая версия:

`3.2.0.4351`

Поведение:

- Если версия ровно `3.2.0.4351`, предупреждение не показывается
- Если версия ниже `3.2.0.4351`, выводится предупреждение о возможной некорректной работе патчера
- Если версия отличается от `3.2.0.4351`, но выше нее, предупреждение тоже будет показано
- Если версию не удалось прочитать из реестра, также выводится предупреждение

Эта проверка носит информационный характер и сама по себе не блокирует патчинг.

## 🖥️ Главное меню

При запуске без аргументов программа показывает:

- Папку Affinity по умолчанию
- Путь к `libaffinity.dll` по умолчанию
- Найден ли целевой файл по умолчанию
- Запатчен ли уже файл по умолчанию
- Установленную версию Affinity
- Предупреждение о совместимости версии, если это нужно

Пункты меню:

- `1` Патч `libaffinity.dll` по умолчанию
- `2` Патч своего файла или папки
- `3` Открыть репозиторий GitHub
- `0` Выход

## 🚀 Использование

Интерактивный режим:

```powershell
python main.py
```

Патч конкретного DLL-файла:

```powershell
python main.py "C:\Path\To\libaffinity.dll"
```

Патч папки, в которой находится `libaffinity.dll`:

```powershell
python main.py "C:\Path\To\Affinity"
```

Если программа собрана в исполняемый файл, она принимает тот же одиночный аргумент с путем.

## 🛡️ Проверки безопасности

Перед записью любых изменений программа:

- Проверяет, что целевой файл существует
- Проверяет, что размер файла достаточен для указанного смещения
- Читает байты по адресу `0x0043E451`
- Останавливается, если файл уже запатчен
- Останавливается, если байты не совпадают с ожидаемой оригинальной сигнатурой
- Создает `libaffinity.dll.bak`, если резервной копии еще нет

Если файл изменится между проверкой и записью, применение патча будет отменено.

## 🔐 Права доступа

Целевой файл по умолчанию находится внутри `Program Files`, поэтому могут понадобиться права администратора.

На Windows скрипт пытается перезапустить себя с повышением прав, если это необходимо.

## 📝 Примечания

- Этот проект рассчитан на Windows
- Скрипт использует только стандартную библиотеку Python
- Используйте на свой риск при патчинге версий, отличающихся от `3.2.0.4351`

## 🛠️ Сборка
Требуется `pyinstaller`:
```bash
pip install -r requirements.txt
Windows: pyinstaller --onefile --uac-admin --icon=icon.ico --name="Open_Affinity_Patcher_Windows" --noupx --clean --version-file=version.txt main.py
```

# 📜 Лицензия

Проект распространяется под лицензией GPL-3.0. Полный текст лицензии содержится в файле [`LICENSE`](LICENSE).

---
# 💰 Поддержать автора
+ **SBER**: `2202 2050 1464 4675`
