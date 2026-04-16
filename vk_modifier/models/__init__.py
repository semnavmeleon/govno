"""
Модуль моделей данных для VK Modifier
Исправленная версия с валидацией и новыми пресетами
"""

import os
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


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
    """
    Класс для хранения настроек обработки с валидацией
    Новые поля для улучшенной обработки аудио
    """
    # Громкость и динамика
    volume: float = 0.0  # dB (-50 to 20)
    normalize: bool = True
    target_loudness: float = -14.0  # LUFS (-24 to -10)
    compress: bool = True
    compress_threshold: float = -20.0  # dB (-60 to 0)
    compress_ratio: float = 4.0  # (1 to 20)
    compress_attack: float = 20.0  # ms (0.1 to 100)
    compress_release: float = 100.0  # ms (10 to 500)
    
    # Эквализация
    bass_gain: float = 0.0  # dB (-20 to 20)
    bass_freq: float = 100.0  # Hz (20 to 500)
    treble_gain: float = 0.0  # dB (-20 to 20)
    treble_freq: float = 10000.0  # Hz (1000 to 20000)
    
    # Скорость и питч
    speed: float = 1.0  # (0.5 to 2.0)
    pitch: float = 0.0  # semitones (-12 to 12)
    
    # Дополнительно
    fade_in: float = 0.0  # seconds (0 to 10)
    fade_out: float = 0.0  # seconds (0 to 10)
    silence_threshold: float = -50.0  # dB (-100 to -20)
    
    # Пресет
    preset_name: str = "safe"
    
    # Для совместимости со старым кодом
    methods: Dict[str, Any] = field(default_factory=dict)
    quality: str = '2'
    preserve_metadata: bool = True
    preserve_cover: bool = True

    def __post_init__(self):
        """Валидация после инициализации"""
        self.validate()
    
    def validate(self):
        """Проверка диапазонов значений"""
        def clamp(val, min_val, max_val, name):
            if val < min_val or val > max_val:
                raise ValueError(f"{name} должен быть в диапазоне [{min_val}, {max_val}], получено {val}")
            return max(min_val, min(val, max_val))
        
        self.volume = clamp(self.volume, -50, 20, "Volume")
        self.target_loudness = clamp(self.target_loudness, -24, -10, "Target Loudness")
        self.compress_threshold = clamp(self.compress_threshold, -60, 0, "Compress Threshold")
        self.compress_ratio = clamp(self.compress_ratio, 1, 20, "Compress Ratio")
        self.compress_attack = clamp(self.compress_attack, 0.1, 100, "Compress Attack")
        self.compress_release = clamp(self.compress_release, 10, 500, "Compress Release")
        
        self.bass_gain = clamp(self.bass_gain, -20, 20, "Bass Gain")
        self.bass_freq = clamp(self.bass_freq, 20, 500, "Bass Freq")
        self.treble_gain = clamp(self.treble_gain, -20, 20, "Treble Gain")
        self.treble_freq = clamp(self.treble_freq, 1000, 20000, "Treble Freq")
        
        self.speed = clamp(self.speed, 0.5, 2.0, "Speed")
        self.pitch = clamp(self.pitch, -12, 12, "Pitch")
        
        self.fade_in = clamp(self.fade_in, 0, 10, "Fade In")
        self.fade_out = clamp(self.fade_out, 0, 10, "Fade Out")
        self.silence_threshold = clamp(self.silence_threshold, -100, -20, "Silence Threshold")
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует настройки в словарь"""
        return {
            "volume": self.volume,
            "normalize": self.normalize,
            "target_loudness": self.target_loudness,
            "compress": self.compress,
            "compress_threshold": self.compress_threshold,
            "compress_ratio": self.compress_ratio,
            "compress_attack": self.compress_attack,
            "compress_release": self.compress_release,
            "bass_gain": self.bass_gain,
            "bass_freq": self.bass_freq,
            "treble_gain": self.treble_gain,
            "treble_freq": self.treble_freq,
            "speed": self.speed,
            "pitch": self.pitch,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "silence_threshold": self.silence_threshold,
            "preset_name": self.preset_name,
            "methods": self.methods,
            "quality": self.quality,
            "preserve_metadata": self.preserve_metadata,
            "preserve_cover": self.preserve_cover
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingSettings':
        """Создает настройки из словаря"""
        return cls(**data)


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
