"""Менеджер конфигурации — сохраняет ВСЕ параметры между сессиями."""

import json
import os
import logging
from .constants import CONFIG_FILE, DEFAULT_FILENAME_TEMPLATE, DEFAULT_TITLE_TEMPLATE

logger = logging.getLogger('vk_modifier.config')

DEFAULTS = {
    # Папки
    'output_dir': '',
    'last_input_dir': '',

    # Окно
    'window_geometry': None,
    'theme': 'dark',

    # Эффекты (нейтральное значение = выключено)
    'pitch_semitones': 0.0,
    'speed_factor': 1.0,
    'eq_preset_index': -1,
    'compression_enabled': False,
    'phase_delay_ms': 0.0,
    'noise_amplitude': 0.0,
    'ultrasound_enabled': False,
    'dc_shift_enabled': False,
    'fade_in_sec': 0,
    'fade_out_sec': 0,

    # Структура
    'trim_start_sec': 0,
    'cut_start_sec': 0.0,
    'cut_end_sec': 0.0,
    'silence_end_sec': 0,
    'merge_enabled': False,
    'merge_track_path': '',

    # Экспорт
    'quality': '2',
    'bitrate_jitter': False,
    'frame_shift': False,
    'broken_duration_enabled': False,
    'broken_duration_type': 0,

    # Метаданные / теги
    'fake_metadata': False,
    'reorder_tags': False,
    'preserve_metadata': True,
    'preserve_cover': True,
    'reupload': False,

    # Брендирование
    'filename_template': DEFAULT_FILENAME_TEMPLATE,
    'title_template': DEFAULT_TITLE_TEMPLATE,
    'brand_prefix': '',
    'brand_tag': '',
    'brand_artist': '',
    'brand_album': '',
    'brand_year': '',
    'brand_genre': '',
    'brand_title': '',
    'cover_mode': 'original',
    'cover_path': '',

    # Обработка
    'max_workers': 2,
    'delete_originals': False,

    # Пресеты (пользовательские)
    'custom_presets': {},
    'last_preset': 'enhanced',

    # Профили папок
    'folder_profiles': {},
}


class Config:
    """Синглтон конфигурации."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = dict(DEFAULTS)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self._data.update(saved)
                logger.info(f"Конфиг загружен: {CONFIG_FILE}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфига: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Конфиг сохранён")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфига: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value

    def get_all(self):
        return dict(self._data)

    def reset(self):
        self._data = dict(DEFAULTS)
        self.save()

    # Пресеты
    def save_preset(self, name, settings):
        presets = self._data.get('custom_presets', {})
        presets[name] = settings
        self._data['custom_presets'] = presets
        self.save()

    def get_preset(self, name):
        return self._data.get('custom_presets', {}).get(name)

    def delete_preset(self, name):
        presets = self._data.get('custom_presets', {})
        presets.pop(name, None)
        self._data['custom_presets'] = presets
        self.save()

    def list_presets(self):
        return list(self._data.get('custom_presets', {}).keys())

    # Профили папок
    def save_folder_profile(self, folder_path, settings):
        profiles = self._data.get('folder_profiles', {})
        profiles[folder_path] = settings
        self._data['folder_profiles'] = profiles
        self.save()

    def get_folder_profile(self, folder_path):
        return self._data.get('folder_profiles', {}).get(folder_path)

    def list_folder_profiles(self):
        return list(self._data.get('folder_profiles', {}).keys())
