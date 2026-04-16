"""Модель данных трека."""

import os
import hashlib
import logging
from dataclasses import dataclass, field

logger = logging.getLogger('vk_modifier.track_info')


@dataclass
class TrackInfo:
    """Информация об одном MP3-файле."""

    file_path: str
    file_name: str = ''
    size_mb: float = 0.0
    duration_sec: float = 0.0
    title: str = ''
    artist: str = ''
    album: str = ''
    year: str = ''
    genre: str = ''
    cover_data: bytes | None = None
    cover_mime: str = 'image/jpeg'
    bitrate: int = 0
    sample_rate: int = 0
    channels: int = 0
    file_hash: str = ''
    # Per-file overrides (None = использовать глобальные настройки)
    custom_cover_data: bytes | None = None
    custom_cover_mime: str | None = None

    def __post_init__(self):
        self.file_name = os.path.basename(self.file_path)
        if os.path.exists(self.file_path):
            self.size_mb = os.path.getsize(self.file_path) / (1024 * 1024)

    def compute_hash(self):
        """Вычислить MD5 хеш файла (первые 8 символов)."""
        try:
            h = hashlib.md5()
            with open(self.file_path, 'rb') as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            self.file_hash = h.hexdigest()[:8]
        except Exception as e:
            logger.warning(f"Hash error {self.file_name}: {e}")
            self.file_hash = '????????'

    def load_metadata(self):
        """Загрузить ID3 теги и технические параметры."""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import APIC

            audio = MP3(self.file_path)
            self.duration_sec = audio.info.length
            self.bitrate = audio.info.bitrate
            self.sample_rate = audio.info.sample_rate
            self.channels = audio.info.channels if hasattr(audio.info, 'channels') else 2

            if audio.tags:
                tag_map = {
                    'TIT2': 'title', 'TPE1': 'artist', 'TALB': 'album',
                    'TDRC': 'year', 'TCON': 'genre',
                }
                for tag_key, attr in tag_map.items():
                    if tag_key in audio.tags:
                        setattr(self, attr, str(audio.tags[tag_key]))

                # Обложка
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        self.cover_data = tag.data
                        self.cover_mime = tag.mime or 'image/jpeg'
                        break

        except Exception as e:
            logger.warning(f"Metadata error {self.file_name}: {e}")

    def get_effective_cover(self) -> tuple[bytes | None, str]:
        """Получить обложку (кастомная или оригинальная)."""
        if self.custom_cover_data is not None:
            return self.custom_cover_data, self.custom_cover_mime or 'image/jpeg'
        return self.cover_data, self.cover_mime

    @property
    def duration_str(self) -> str:
        if self.duration_sec <= 0:
            return "?"
        m, s = divmod(int(self.duration_sec), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @property
    def bitrate_str(self) -> str:
        if self.bitrate <= 0:
            return "?"
        return f"{self.bitrate // 1000} kbps"

    @property
    def summary(self) -> str:
        """Краткая строка для списка файлов."""
        return f"{self.file_name}\n{self.size_mb:.1f} MB · {self.duration_str}"

    @property
    def detail_info(self) -> str:
        """Подробная информация для панели инфо."""
        lines = [
            f"Файл: {self.file_name}",
            f"Размер: {self.size_mb:.2f} MB",
            f"MD5: {self.file_hash}",
        ]
        if self.duration_sec > 0:
            lines.append(f"Длительность: {self.duration_str}")
        if self.bitrate:
            lines.append(f"Битрейт: {self.bitrate_str}")
        if self.sample_rate:
            lines.append(f"Sample rate: {self.sample_rate} Hz")
        if self.channels:
            lines.append(f"Каналы: {self.channels}")
        if self.artist or self.title:
            lines.append(f"Оригинал: {self.artist} — {self.title}")
        if self.album:
            lines.append(f"Альбом: {self.album}")
        if self.year:
            lines.append(f"Год: {self.year}")
        if self.genre:
            lines.append(f"Жанр: {self.genre}")
        lines.append(f"Обложка: {'Есть' if self.cover_data else 'Нет'}")
        return "\n".join(lines)
