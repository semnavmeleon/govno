"""
Модуль утилит для VK Modifier
"""

import os
import json
import sys
from typing import Dict, Any, Optional

from vk_modifier.processors import PRESETS

CONFIG_FILE = "vk_modifier_config.json"


class PresetManager:
    """Менеджер пресетов обработки"""
    
    def __init__(self):
        self.presets = PRESETS.copy()
    
    def get_preset_names(self) -> list:
        """Возвращает список имен пресетов"""
        return list(self.presets.keys())
    
    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """Возвращает информацию о пресете"""
        if preset_name in self.presets:
            return {
                "name": self.presets[preset_name]["name"],
                "description": self.presets[preset_name]["description"],
                "settings": self.presets[preset_name]["settings"].copy()
            }
        raise ValueError(f"Preset '{preset_name}' not found")
    
    def apply_preset(self, preset_name: str) -> Dict[str, Any]:
        """Применяет пресет и возвращает настройки"""
        if preset_name not in self.presets:
            raise ValueError(f"Preset '{preset_name}' not found")
        return self.presets[preset_name]["settings"].copy()


class ConfigManager:
    """Класс для управления конфигурацией"""

    DEFAULT_CONFIG = {
        'output_dir': '',
        'pitch_value': 1,
        'silence_duration': 45,
        'speed_value': 1.01,
        'eq_value': 3,
        'quality': '2',
        'preserve_metadata': True,
        'preserve_cover': True,
        'preset_name': 'safe'  # Новый пресет по умолчанию
    }

    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.preset_manager = PresetManager()

    def load(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"Error loading config: {e}")
        return self.config.copy()

    def save(self, config: Optional[Dict[str, Any]] = None):
        """Сохраняет конфигурацию в файл"""
        if config:
            self.config.update(config)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение из конфигурации"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Устанавливает значение в конфигурации"""
        self.config[key] = value


class MetadataExtractor:
    """Класс для извлечения метаданных из MP3 файлов"""

    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из MP3 файла

        Returns:
            Словарь с метаданными
        """
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3

        metadata = {
            'title': '',
            'artist': '',
            'album': '',
            'year': '',
            'genre': '',
            'duration': 0.0,
            'bitrate': 0,
            'sample_rate': 0,
            'has_cover': False
        }

        try:
            audio = MP3(file_path)
            metadata['duration'] = audio.info.length
            metadata['bitrate'] = audio.info.bitrate
            metadata['sample_rate'] = audio.info.sample_rate

            if audio.tags:
                from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TCON, APIC

                if 'TIT2' in audio.tags:
                    metadata['title'] = str(audio.tags['TIT2'])
                if 'TPE1' in audio.tags:
                    metadata['artist'] = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    metadata['album'] = str(audio.tags['TALB'])
                if 'TDRC' in audio.tags:
                    metadata['year'] = str(audio.tags['TDRC'])
                if 'TCON' in audio.tags:
                    metadata['genre'] = str(audio.tags['TCON'])

                # Проверка наличия обложки
                for tag in audio.tags.values():
                    if hasattr(tag, 'mime') and hasattr(tag, 'data'):
                        metadata['has_cover'] = True
                        break

        except Exception as e:
            print(f"Error extracting metadata: {e}")

        return metadata

    @staticmethod
    def extract_cover(file_path: str) -> tuple:
        """
        Извлекает обложку из MP3 файла

        Returns:
            Кортеж (cover_data, mime_type) или (None, None) если обложки нет
        """
        from mutagen.mp3 import MP3
        from mutagen.id3 import APIC

        try:
            audio = MP3(file_path)
            if audio.tags:
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        return tag.data, tag.mime
        except Exception as e:
            print(f"Error extracting cover: {e}")

        return None, None


class PresetManager:
    """Класс для управления пресетами обработки"""

    PRESETS = {
        'enhanced': {
            'trim_silence': False,
            'cut_fragment': False,
            'fade_out': False,
            'broken_duration': True,
            'broken_type': 0,
            'pitch': False,
            'silence': False,
            'speed': True,
            'speed_value': 1.01,
            'eq': False,
            'phase': False,
            'noise': False,
            'compression': False,
            'ultrasound': False,
            'dc_shift': False,
            'merge': False,
            'bitrate_jitter': True,
            'frame_shift': False,
            'fake_metadata': True,
            'reorder_tags': True,
            'reupload': True,
            'quality': '0',
            'rename_files': False,
            'preserve_metadata': False,
            'preserve_cover': False
        },
        'reupload': {
            'trim_silence': False,
            'cut_fragment': False,
            'fade_out': False,
            'broken_duration': True,
            'broken_type': 1,
            'pitch': False,
            'silence': False,
            'speed': False,
            'eq': False,
            'phase': False,
            'noise': False,
            'compression': False,
            'ultrasound': False,
            'dc_shift': False,
            'merge': False,
            'bitrate_jitter': False,
            'frame_shift': False,
            'fake_metadata': False,
            'reorder_tags': False,
            'reupload': True,
            'quality': '0',
            'rename_files': False,
            'preserve_metadata': True,
            'preserve_cover': True
        }
    }

    @classmethod
    def get_preset(cls, name: str) -> Optional[Dict[str, Any]]:
        """Получает пресет по имени"""
        return cls.PRESETS.get(name)

    @classmethod
    def get_preset_names(cls) -> list:
        """Получает список имён пресетов"""
        return list(cls.PRESETS.keys())

    @classmethod
    def apply_preset(cls, name: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Применяет пресет к настройкам"""
        preset = cls.get_preset(name)
        if preset:
            settings.update(preset)
        return settings


def check_ffmpeg() -> bool:
    """Проверяет доступность FFmpeg"""
    import subprocess

    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            check=True,
            encoding='utf-8',
            errors='ignore'
        )
        return True
    except Exception:
        pass

    # Проверка bundled ffmpeg для frozen приложений
    if getattr(sys, 'frozen', False):
        app_path = os.path.dirname(sys.executable)
        ffmpeg_path = os.path.join(app_path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            try:
                subprocess.run(
                    [ffmpeg_path, '-version'],
                    capture_output=True,
                    check=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                return True
            except Exception:
                pass

    return False


def get_quality_map() -> Dict[int, str]:
    """Получает маппинг качества MP3"""
    return {0: '0', 1: '2', 2: '5', 3: '7'}


def get_pitch_values() -> list:
    """Получает список значений pitch shift"""
    return [-2, -1, 1, 2, -0.5, 0.5]


def get_speed_values() -> list:
    """Получает список значений скорости"""
    return [0.97, 0.98, 0.99, 1.01, 1.02, 1.03, 0.995, 1.005]


def get_eq_values() -> list:
    """Получает список значений эквалайзера"""
    return [2, 4, 6, 4, -3]


def get_phase_values() -> list:
    """Получает список значений фазового сдвига"""
    return [0.3, 0.5, 0.8]


def get_noise_values() -> list:
    """Получает список значений шума"""
    return [0.0005, 0.001, 0.002]
