"""
Модуль моделей данных для VK Modifier
"""

import os
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrackInfo:
    """Класс для хранения информации о треке"""
    file_path: str
    file_name: str = field(init=False)
    size_mb: float = field(init=False)
    duration_sec: float = 0.0
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""
    cover_data: Optional[bytes] = None
    cover_mime: str = "image/jpeg"
    bitrate: int = 0
    sample_rate: int = 0
    file_hash: str = ""

    def __post_init__(self):
        self.file_name = os.path.basename(self.file_path)
        self.size_mb = os.path.getsize(self.file_path) / (1024 * 1024)

    def set_hash(self, data: bytes):
        """Устанавливает MD5 хеш файла"""
        self.file_hash = hashlib.md5(data).hexdigest()[:8]


@dataclass
class ProcessingSettings:
    """Класс для хранения настроек обработки"""
    # Основные методы
    trim_silence: bool = False
    cut_fragment: bool = False
    fade_out: bool = False
    broken_duration: bool = False
    pitch: bool = False
    silence: bool = False
    speed: bool = False
    eq: bool = False
    phase: bool = False
    noise: bool = False
    compression: bool = False
    ultrasound: bool = False
    dc_shift: bool = False
    merge: bool = False
    bitrate_jitter: bool = False
    frame_shift: bool = False
    fake_metadata: bool = False
    reorder_tags: bool = False

    # Параметры методов
    broken_type: int = 0
    trim_duration: int = 5
    cut_position_percent: int = 50
    cut_duration: int = 2
    fade_duration: int = 5
    pitch_value: float = -1.0
    silence_duration: int = 45
    speed_value: float = 1.01
    eq_value: int = 4
    eq_type: int = 1
    phase_value: float = 0.5
    noise_value: float = 0.0005
    quality: str = '2'

    # Общие настройки
    preserve_metadata: bool = True
    preserve_cover: bool = True
    rename_files: bool = True
    delete_original: bool = False
    reupload: bool = False
    extra_track_path: str = ""

    def to_dict(self) -> dict:
        """Конвертирует настройки в словарь"""
        return {
            'methods': {
                'trim_silence': self.trim_silence,
                'cut_fragment': self.cut_fragment,
                'fade_out': self.fade_out,
                'broken_duration': self.broken_duration,
                'pitch': self.pitch,
                'silence': self.silence,
                'speed': self.speed,
                'eq': self.eq,
                'phase': self.phase,
                'noise': self.noise,
                'compression': self.compression,
                'ultrasound': self.ultrasound,
                'dc_shift': self.dc_shift,
                'merge': self.merge,
                'bitrate_jitter': self.bitrate_jitter,
                'frame_shift': self.frame_shift,
                'fake_metadata': self.fake_metadata,
                'reorder_tags': self.reorder_tags
            },
            'broken_type': self.broken_type,
            'trim_duration': self.trim_duration,
            'cut_position_percent': self.cut_position_percent,
            'cut_duration': self.cut_duration,
            'fade_duration': self.fade_duration,
            'pitch_value': self.pitch_value,
            'silence_duration': self.silence_duration,
            'speed_value': self.speed_value,
            'eq_value': self.eq_value,
            'eq_type': self.eq_type,
            'phase_value': self.phase_value,
            'noise_value': self.noise_value,
            'quality': self.quality,
            'preserve_metadata': self.preserve_metadata,
            'preserve_cover': self.preserve_cover,
            'rename_files': self.rename_files,
            'delete_original': self.delete_original,
            'reupload': self.reupload,
            'extra_track_path': self.extra_track_path if self.merge else ""
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessingSettings':
        """Создаёт объект настроек из словаря"""
        settings = cls()
        
        methods = data.get('methods', {})
        settings.trim_silence = methods.get('trim_silence', False)
        settings.cut_fragment = methods.get('cut_fragment', False)
        settings.fade_out = methods.get('fade_out', False)
        settings.broken_duration = methods.get('broken_duration', False)
        settings.pitch = methods.get('pitch', False)
        settings.silence = methods.get('silence', False)
        settings.speed = methods.get('speed', False)
        settings.eq = methods.get('eq', False)
        settings.phase = methods.get('phase', False)
        settings.noise = methods.get('noise', False)
        settings.compression = methods.get('compression', False)
        settings.ultrasound = methods.get('ultrasound', False)
        settings.dc_shift = methods.get('dc_shift', False)
        settings.merge = methods.get('merge', False)
        settings.bitrate_jitter = methods.get('bitrate_jitter', False)
        settings.frame_shift = methods.get('frame_shift', False)
        settings.fake_metadata = methods.get('fake_metadata', False)
        settings.reorder_tags = methods.get('reorder_tags', False)
        
        settings.broken_type = data.get('broken_type', 0)
        settings.trim_duration = data.get('trim_duration', 5)
        settings.cut_position_percent = data.get('cut_position_percent', 50)
        settings.cut_duration = data.get('cut_duration', 2)
        settings.fade_duration = data.get('fade_duration', 5)
        settings.pitch_value = data.get('pitch_value', -1.0)
        settings.silence_duration = data.get('silence_duration', 45)
        settings.speed_value = data.get('speed_value', 1.01)
        settings.eq_value = data.get('eq_value', 4)
        settings.eq_type = data.get('eq_type', 1)
        settings.phase_value = data.get('phase_value', 0.5)
        settings.noise_value = data.get('noise_value', 0.0005)
        settings.quality = data.get('quality', '2')
        settings.preserve_metadata = data.get('preserve_metadata', True)
        settings.preserve_cover = data.get('preserve_cover', True)
        settings.rename_files = data.get('rename_files', True)
        settings.delete_original = data.get('delete_original', False)
        settings.reupload = data.get('reupload', False)
        settings.extra_track_path = data.get('extra_track_path', '')
        
        return settings


@dataclass
class Metadata:
    """Класс для хранения метаданных трека"""
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""

    def to_dict(self) -> dict:
        """Конвертирует метаданные в словарь"""
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'year': self.year,
            'genre': self.genre
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Metadata':
        """Создаёт объект метаданных из словаря"""
        return cls(
            title=data.get('title', ''),
            artist=data.get('artist', ''),
            album=data.get('album', ''),
            year=data.get('year', ''),
            genre=data.get('genre', '')
        )
