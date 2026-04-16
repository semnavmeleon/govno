"""Обёртка над ffmpeg: поиск бинарника, скрытый запуск, таймаут."""

import subprocess
import sys
import os
import logging
import shutil

from ..constants import BASE_DIR, RESOURCES_DIR

logger = logging.getLogger('vk_modifier.ffmpeg')

# Windows: скрыть окно консоли
_STARTUPINFO = None
_CREATION_FLAGS = 0
if sys.platform == 'win32':
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW

_ffmpeg_path = None


def find_ffmpeg() -> str | None:
    """Найти ffmpeg. Приоритет: ресурсы PyInstaller → рядом с exe → PATH."""
    global _ffmpeg_path
    if _ffmpeg_path:
        return _ffmpeg_path

    candidates = []

    # 1. Встроенный бинарник (PyInstaller resources)
    if hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, 'ffmpeg.exe'))
        candidates.append(os.path.join(sys._MEIPASS, 'resources', 'ffmpeg.exe'))

    # 2. Рядом с программой
    candidates.append(os.path.join(BASE_DIR, 'ffmpeg.exe'))
    candidates.append(os.path.join(BASE_DIR, 'ffmpeg'))
    candidates.append(os.path.join(RESOURCES_DIR, 'ffmpeg.exe'))

    for c in candidates:
        if os.path.isfile(c):
            if _test_ffmpeg(c):
                _ffmpeg_path = c
                logger.info(f"FFmpeg найден (локальный): {c}")
                return _ffmpeg_path

    # 3. В PATH
    found = shutil.which('ffmpeg')
    if found and _test_ffmpeg(found):
        _ffmpeg_path = found
        logger.info(f"FFmpeg найден (PATH): {found}")
        return _ffmpeg_path

    logger.error("FFmpeg не найден")
    return None


def _test_ffmpeg(path: str) -> bool:
    """Проверить что бинарник рабочий."""
    try:
        r = subprocess.run(
            [path, '-version'],
            capture_output=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=_STARTUPINFO,
            creationflags=_CREATION_FLAGS,
            timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def get_ffmpeg_version() -> str:
    """Получить версию ffmpeg для status bar."""
    path = find_ffmpeg()
    if not path:
        return "не найден"
    try:
        r = subprocess.run(
            [path, '-version'],
            capture_output=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=_STARTUPINFO,
            creationflags=_CREATION_FLAGS,
            timeout=10,
        )
        first_line = r.stdout.split('\n')[0] if r.stdout else ''
        # "ffmpeg version 6.1.1 ..." → "6.1.1"
        parts = first_line.split()
        for i, p in enumerate(parts):
            if p == 'version' and i + 1 < len(parts):
                return parts[i + 1]
        return first_line[:40]
    except Exception:
        return "ошибка"


def run_ffmpeg(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    """
    Запуск ffmpeg без окна консоли.

    args: аргументы БЕЗ 'ffmpeg' в начале (добавляется автоматически).
    timeout: таймаут в секундах.
    Raises: FileNotFoundError если ffmpeg не найден.
            subprocess.TimeoutExpired если таймаут.
    """
    path = find_ffmpeg()
    if not path:
        raise FileNotFoundError("FFmpeg не найден. Поместите ffmpeg.exe рядом с программой.")

    cmd = [path] + args

    # Полное логирование команды
    cmd_str = ' '.join(f'"{a}"' if ' ' in a else a for a in cmd)
    logger.info(f"FFmpeg cmd: {cmd_str}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        encoding='utf-8',
        errors='ignore',
        startupinfo=_STARTUPINFO,
        creationflags=_CREATION_FLAGS,
        timeout=timeout,
    )

    if result.returncode != 0:
        logger.warning(f"FFmpeg exit={result.returncode}\nstderr: {result.stderr[:500]}")
    else:
        logger.debug(f"FFmpeg OK: {os.path.basename(args[-1]) if args else '?'}")

    return result


def probe_file(file_path: str) -> dict | None:
    """Получить информацию о файле через ffprobe."""
    path = find_ffmpeg()
    if not path:
        return None

    # ffprobe рядом с ffmpeg
    probe_path = path.replace('ffmpeg', 'ffprobe')
    if not os.path.isfile(probe_path):
        probe_path = shutil.which('ffprobe')
    if not probe_path:
        return None

    try:
        import json
        r = subprocess.run(
            [probe_path, '-v', 'quiet', '-print_format', 'json',
             '-show_format', '-show_streams', file_path],
            capture_output=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=_STARTUPINFO,
            creationflags=_CREATION_FLAGS,
            timeout=30,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception as e:
        logger.warning(f"ffprobe error: {e}")
    return None


def generate_spectrogram(input_file: str, output_png: str,
                         width: int = 800, height: int = 200) -> bool:
    """Сгенерировать спектрограмму (PNG) через ffmpeg showspectrumpic."""
    try:
        result = run_ffmpeg([
            '-i', input_file,
            '-lavfi', f'showspectrumpic=s={width}x{height}:mode=combined:color=intensity',
            '-y', output_png,
        ], timeout=60)
        return result.returncode == 0 and os.path.isfile(output_png)
    except Exception as e:
        logger.warning(f"Spectrogram error: {e}")
        return False


def get_audio_fingerprint(file_path: str) -> str | None:
    """Получить акустический хеш (MD5 PCM-потока) через ffmpeg."""
    try:
        result = run_ffmpeg([
            '-i', file_path,
            '-f', 'md5', '-ac', '1', '-ar', '8000',
            '-',
        ], timeout=30)
        if result.returncode == 0 and result.stdout:
            # Output: "MD5=<hash>"
            line = result.stdout.strip()
            if '=' in line:
                return line.split('=', 1)[1].strip()
        return None
    except Exception:
        return None
