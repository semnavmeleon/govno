"""Система брендирования: шаблоны имён, метаданных, управление обложками."""

import os
import re
import random
import string
import logging
from datetime import date
from io import BytesIO

logger = logging.getLogger('vk_modifier.branding')


class BrandingEngine:
    """Применение шаблонов брендирования к трекам."""

    def __init__(self, settings: dict):
        self.s = settings

    def render_filename(self, track_info, index: int) -> str:
        """Сгенерировать имя файла по шаблону."""
        template = self.s.get('filename_template', '{original_name}')
        if not template.strip():
            template = '{original_name}'

        name_no_ext = os.path.splitext(track_info.file_name)[0]

        # Собрать контекст переменных
        ctx = {
            'original_name': name_no_ext,
            'original_title': track_info.title or name_no_ext,
            'original_artist': track_info.artist or 'Unknown',
            'title': self.s.get('brand_title') or track_info.title or name_no_ext,
            'artist': self.s.get('brand_artist') or track_info.artist or 'Unknown',
            'album': self.s.get('brand_album') or track_info.album or '',
            'year': self.s.get('brand_year') or track_info.year or '',
            'genre': self.s.get('brand_genre') or track_info.genre or '',
            'counter': index + 1,
            'md5_short': track_info.file_hash[:6] if track_info.file_hash else '000000',
            'date': date.today().isoformat(),
            'prefix': self.s.get('brand_prefix', ''),
            'tag': self.s.get('brand_tag', ''),
            'random': ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)),
        }

        result = self._safe_format(template, ctx)
        # Очистить от невалидных символов для имени файла
        result = self._sanitize_filename(result)
        return result + '.mp3'

    def render_title(self, track_info) -> str:
        """Сгенерировать title метаданные по шаблону."""
        template = self.s.get('title_template', '{original_title}')
        if not template.strip():
            return track_info.title or ''

        ctx = {
            'original_title': track_info.title or '',
            'original_artist': track_info.artist or '',
            'tag': self.s.get('brand_tag', ''),
            'prefix': self.s.get('brand_prefix', ''),
            'random': ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)),
        }

        result = self._safe_format(template, ctx)
        # Убрать пустые скобки если tag/prefix пустые
        result = re.sub(r'\(\s*\)', '', result)
        result = re.sub(r'\[\s*\]', '', result)
        return result.strip()

    def get_metadata_args(self, track_info) -> list[str]:
        """Собрать -metadata аргументы для ffmpeg."""
        args = []
        user_meta = self.s.get('user_metadata', {})

        # Title: приоритет — user_meta > brand_title > template > preserve
        title = user_meta.get('title', '') or self.s.get('brand_title', '')
        if not title:
            title = self.render_title(track_info)
        elif not title and self.s.get('preserve_metadata'):
            title = track_info.title

        # REUPLOAD суффикс (как в v1)
        if self.s.get('reupload') and title:
            title = f"{title} (REUPLOAD)"

        if title:
            args.extend(['-metadata', f'title={title}'])

        # Artist
        artist = user_meta.get('artist', '') or self.s.get('brand_artist', '')
        if not artist and self.s.get('preserve_metadata'):
            artist = track_info.artist
        if artist:
            args.extend(['-metadata', f'artist={artist}'])

        # Album
        album = user_meta.get('album', '') or self.s.get('brand_album', '')
        if not album and self.s.get('preserve_metadata'):
            album = track_info.album
        if album:
            args.extend(['-metadata', f'album={album}'])

        # Year
        year = user_meta.get('year', '') or self.s.get('brand_year', '')
        if not year and self.s.get('preserve_metadata'):
            year = track_info.year
        if year:
            args.extend(['-metadata', f'date={year}'])

        # Genre
        genre = user_meta.get('genre', '') or self.s.get('brand_genre', '')
        if not genre and self.s.get('preserve_metadata'):
            genre = track_info.genre
        if genre:
            args.extend(['-metadata', f'genre={genre}'])

        # Fake metadata
        if self.s.get('fake_metadata'):
            fake = ''.join(random.choices(
                string.ascii_letters + string.digits + ' ', k=random.randint(100, 500)
            ))
            args.extend(['-metadata', f'comment={fake}'])

        return args

    def _safe_format(self, template: str, ctx: dict) -> str:
        """Безопасный format — пропускает неизвестные переменные."""
        try:
            # Поддержка {counter:03d} и обычных {name}
            return template.format(**ctx)
        except (KeyError, ValueError, IndexError):
            # Фолбэк: ручная подстановка
            result = template
            for key, val in ctx.items():
                result = result.replace('{' + key + '}', str(val))
            return result

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Убрать невалидные символы из имени файла."""
        # Удалить символы запрещённые в Windows
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Удалить начальные/конечные пробелы и точки
        name = name.strip(' .')
        # Заменить множественные пробелы
        name = re.sub(r'\s+', ' ', name)
        return name or 'track'

    @staticmethod
    def resize_cover(data: bytes, max_size: int = 500) -> bytes:
        """Ресайз обложки до max_size x max_size с сохранением пропорций."""
        try:
            from PyQt5.QtGui import QPixmap, QImage
            from PyQt5.QtCore import Qt

            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if pixmap.isNull():
                return data

            if pixmap.width() <= max_size and pixmap.height() <= max_size:
                return data

            scaled = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            buf = BytesIO()
            from PyQt5.QtCore import QBuffer, QIODevice
            qbuf = QBuffer()
            qbuf.open(QIODevice.WriteOnly)
            scaled.save(qbuf, 'JPEG', 90)
            return bytes(qbuf.data())

        except Exception as e:
            logger.warning(f"Cover resize error: {e}")
            return data
