"""Система пресетов: встроенные + пользовательские + импорт/экспорт."""

import json
import logging
from datetime import date
from ..config import Config
from ..constants import APP_VERSION

logger = logging.getLogger('vk_modifier.presets')

# Встроенные пресеты — только отличия от дефолтов
BUILTIN_PRESETS = {
    'enhanced': {
        'label': 'Расширенный',
        'description': 'Скорость + jitter + fake meta + broken duration',
        'settings': {
            'speed_factor': 1.01,
            'bitrate_jitter': True,
            'fake_metadata': True,
            'reorder_tags': True,
            'broken_duration_enabled': True,
            'broken_duration_type': 0,
            'quality': '0',
            'preserve_metadata': False,
            'preserve_cover': False,
            'brand_tag': 'REUPLOAD',
        },
    },
    'reupload': {
        'label': 'Reupload',
        'description': 'Broken duration + тег REUPLOAD',
        'settings': {
            'broken_duration_enabled': True,
            'broken_duration_type': 1,
            'quality': '0',
            'brand_tag': 'REUPLOAD',
        },
    },
    'stealth': {
        'label': 'Невидимка',
        'description': 'Максимальные изменения при минимальной слышимости',
        'settings': {
            'speed_factor': 1.005,
            'pitch_semitones': 0.5,
            'noise_amplitude': 0.0008,
            'ultrasound_enabled': True,
            'dc_shift_enabled': True,
            'bitrate_jitter': True,
            'fake_metadata': True,
            'reorder_tags': True,
            'frame_shift': True,
        },
    },
    'minimal': {
        'label': 'Минимальный',
        'description': 'Только перекодирование и fake metadata',
        'settings': {
            'fake_metadata': True,
            'quality': '0',
        },
    },
}


def get_preset_settings(name: str) -> dict | None:
    """Получить настройки пресета (встроенного или пользовательского)."""
    if name in BUILTIN_PRESETS:
        return dict(BUILTIN_PRESETS[name]['settings'])
    config = Config()
    custom = config.get_preset(name)
    if custom:
        return dict(custom)
    return None


def list_all_presets() -> list[dict]:
    """Список всех пресетов: [{name, label, description, builtin}]."""
    result = []
    for name, data in BUILTIN_PRESETS.items():
        result.append({
            'name': name, 'label': data['label'],
            'description': data['description'], 'builtin': True,
        })
    config = Config()
    for name in config.list_presets():
        result.append({
            'name': name, 'label': name,
            'description': 'Пользовательский пресет', 'builtin': False,
        })
    return result


def export_preset_to_file(name: str, settings: dict, file_path: str):
    """Экспорт пресета в JSON файл."""
    data = {
        'preset_name': name,
        'app_version': APP_VERSION,
        'date': date.today().isoformat(),
        'settings': settings,
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Пресет '{name}' экспортирован в {file_path}")


def import_preset_from_file(file_path: str) -> tuple[str, dict]:
    """Импорт пресета из JSON файла. Возвращает (name, settings)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if 'settings' not in data or not isinstance(data['settings'], dict):
        raise ValueError("Неверный формат файла пресета")
    name = data.get('preset_name', 'imported')
    return name, data['settings']


def export_all_presets(file_path: str):
    """Экспорт всех пользовательских пресетов в один файл."""
    config = Config()
    all_presets = {}
    for name in config.list_presets():
        all_presets[name] = config.get_preset(name)
    data = {
        'app_version': APP_VERSION,
        'date': date.today().isoformat(),
        'presets': all_presets,
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def import_all_presets(file_path: str) -> int:
    """Импорт всех пресетов из файла. Возвращает количество импортированных."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    presets = data.get('presets', {})
    config = Config()
    count = 0
    for name, settings in presets.items():
        if isinstance(settings, dict):
            config.save_preset(name, settings)
            count += 1
    return count
