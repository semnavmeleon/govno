"""Константы и значения по умолчанию."""

import os
import sys

APP_NAME = "VK Track Modifier"
APP_VERSION = "2.1.0"
CONFIG_FILE = "vk_modifier_config.json"

# GitHub для auto-update
GITHUB_REPO = ""  # Заполнить при публикации: "user/vk-track-modifier"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest" if GITHUB_REPO else ""

# Путь к ресурсам (работает и в dev, и в PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCES_DIR = os.path.join(sys._MEIPASS, 'resources')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')

# Шаблоны брендирования по умолчанию
DEFAULT_FILENAME_TEMPLATE = "{prefix}_{counter:03d}_{original_name}"
DEFAULT_TITLE_TEMPLATE = "{original_title} ({tag})"

TEMPLATE_VARS_HELP = {
    '{original_name}': 'Имя файла без расширения',
    '{original_title}': 'Название из тегов',
    '{original_artist}': 'Исполнитель из тегов',
    '{title}': 'Новое название (или оригинальное)',
    '{artist}': 'Новый исполнитель (или оригинальный)',
    '{album}': 'Альбом',
    '{year}': 'Год',
    '{genre}': 'Жанр',
    '{counter}': 'Порядковый номер (поддерживает :03d)',
    '{md5_short}': 'Первые 6 символов MD5',
    '{date}': 'Текущая дата YYYY-MM-DD',
    '{prefix}': 'Пользовательский префикс',
    '{tag}': 'Пользовательский тег (REUPLOAD, REMIX...)',
    '{random}': 'Случайная строка 6 символов',
}

# Диапазоны параметров
PITCH_RANGE = (-2.0, 2.0, 0.5)
SPEED_RANGE = (0.95, 1.05, 0.005)
PHASE_RANGE = (0.0, 1.0, 0.1)
NOISE_RANGE = (0.0, 0.01, 0.0005)
FADE_RANGE = (0, 30, 1)

# Качество кодирования
QUALITY_OPTIONS = {
    '320 kbps': '0',
    '245 kbps': '2',
    '175 kbps': '5',
    '130 kbps': '7',
}

# Broken duration типы
BROKEN_DURATION_TYPES = [
    "1:04:19 (классический)",
    "Смещение +1 час",
    "Смещение x15",
    "Фейковый Xing",
]

# EQ пресеты
EQ_PRESETS = [
    ("Лёгкая коррекция", "equalizer=f=1000:width_type=o:width=2:g=-2"),
    ("Средняя коррекция", "equalizer=f=1000:width_type=o:width=2:g=-4"),
    ("Сильная коррекция", "equalizer=f=1000:width_type=o:width=2:g=-6"),
    ("Boost середины", "equalizer=f=1000:width_type=o:width=2:g=-4,equalizer=f=2000:width_type=o:width=2:g=-2"),
    ("Boost верхов", "equalizer=f=8000:width_type=o:width=2:g=3"),
]

# Обложка
COVER_MAX_SIZE = 500

# Поддерживаемые расширения
SUPPORTED_EXTENSIONS = {'.mp3'}
