"""
Модуль процессоров для обработки аудио
"""

import os
import random
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TLEN, TXXX


class FilterBuilder:
    """Класс для построения FFmpeg аудио фильтров"""

    @staticmethod
    def build_filters(settings: dict) -> Optional[str]:
        """
        Строит строку аудио фильтров для FFmpeg на основе настроек

        Args:
            settings: Словарь с настройками обработки

        Returns:
            Строка фильтров или None если фильтры не нужны
        """
        filters = []

        # Изменение тональности (pitch shift)
        if settings['methods'].get('pitch', False):
            semitones = settings.get('pitch_value', -1.0)
            rate = 44100 * (2 ** (semitones / 12))
            filters.append(f"asetrate={rate:.0f},aresample=44100")

        # Изменение скорости
        if settings['methods'].get('speed', False):
            speed = settings.get('speed_value', 1.01)
            # atempo поддерживает значения от 0.5 до 2.0
            if speed < 0.5:
                speed = 0.5
            elif speed > 2.0:
                speed = 2.0
            filters.append(f"atempo={speed}")

        # Эквализация
        if settings['methods'].get('eq', False):
            eq_type = settings.get('eq_type', 1)
            eq_value = settings.get('eq_value', 4)

            if eq_type == 3:  # Средние частоты
                filters.append("equalizer=f=1000:width_type=o:width=2:g=-4")
                filters.append("equalizer=f=2000:width_type=o:width=2:g=-2")
            elif eq_type == 4:  # Высокие частоты
                filters.append("equalizer=f=8000:width_type=o:width=2:g=3")
            else:  # Обычная эквализация
                filters.append(f"equalizer=f=1000:width_type=o:width=2:g={-eq_value}")

        # Фазовый сдвиг
        if settings['methods'].get('phase', False):
            delay = settings.get('phase_value', 0.5)
            filters.append(f"aphaser=type=t:delay={delay}:decay=0.4")

        # Добавление шума (через softclip)
        if settings['methods'].get('noise', False):
            noise_level = settings.get('noise_value', 0.0005)
            threshold = 1.0 - (noise_level * 200)
            if threshold < 0.1:
                threshold = 0.1
            elif threshold > 0.99:
                threshold = 0.99
            filters.append(f"asoftclip=type=3:threshold={threshold}")

        # Компрессия
        if settings['methods'].get('compression', False):
            filters.append("compand=attacks=0.1:decays=0.1:points=-80/-80|-45/-15|-27/-9|0/-7|20/-7")

        # Ультразвуковой шум (earwax фильтр добавляет фазовые искажения)
        if settings['methods'].get('ultrasound', False):
            filters.append("earwax")

        # DC сдвиг
        if settings['methods'].get('dc_shift', False):
            filters.append("dcshift=0.001")

        # Добавление тишины в конец
        if settings['methods'].get('silence', False):
            silence_dur = settings.get('silence_duration', 45)
            filters.append(f"apad=pad_dur={silence_dur}")

        return ",".join(filters) if filters else None


class AudioProcessor:
    """Класс для обработки аудио файлов"""

    def __init__(self, ffmpeg_path: str = 'ffmpeg'):
        self.ffmpeg_path = ffmpeg_path
        self.temp_files: List[str] = []

    def check_ffmpeg(self) -> bool:
        """Проверяет доступность FFmpeg"""
        try:
            subprocess.run(
                [self.ffmpeg_path, '-version'],
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
                    self.ffmpeg_path = ffmpeg_path
                    return True
                except Exception:
                    pass

        return False

    def get_audio_duration(self, file_path: str) -> float:
        """Получает длительность аудио файла в секундах"""
        try:
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting duration: {e}")
        return 0.0

    def trim_silence(self, input_path: str, trim_seconds: int) -> str:
        """Обрезает тишину в начале трека"""
        output = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        output.close()
        self.temp_files.append(output.name)

        cmd = [
            self.ffmpeg_path, '-i', input_path,
            '-ss', f'00:00:{trim_seconds}',
            '-codec:a', 'libmp3lame', '-q:a', '2',
            '-y', output.name
        ]
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            raise Exception(f"FFmpeg trim error: {result.stderr}")
        return output.name

    def cut_fragment(
        self,
        input_path: str,
        position_percent: int,
        cut_duration: int
    ) -> str:
        """Вырезает фрагмент из трека"""
        duration = self.get_audio_duration(input_path)
        if duration <= 0:
            return input_path

        cut_start = (duration * position_percent / 100) - (cut_duration / 2)
        if cut_start < 0:
            cut_start = 0
        cut_end = cut_start + cut_duration

        output = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        output.close()
        self.temp_files.append(output.name)

        # Используем более простой подход с двумя фильтрами
        filter_complex = (
            f"[0:a]atrim=0:{cut_start},asetpts=PTS-STARTPTS[f];"
            f"[0:a]atrim={cut_end}:,asetpts=PTS-STARTPTS[s];"
            f"[f][s]concat=n=2:v=0:a=1[out]"
        )

        cmd = [
            self.ffmpeg_path, '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-codec:a', 'libmp3lame', '-q:a', '2',
            '-y', output.name
        ]
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            raise Exception(f"FFmpeg cut error: {result.stderr}")
        return output.name

    def merge_tracks(self, primary_track: str, extra_track: str) -> str:
        """Сращивает два трека"""
        # Создаём файл списка для concat demuxer
        concat_list = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        )
        concat_list.write(f"file '{primary_track}'\n")
        concat_list.write(f"file '{extra_track}'")
        concat_list.close()
        self.temp_files.append(concat_list.name)

        output = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        output.close()
        self.temp_files.append(output.name)

        cmd = [
            self.ffmpeg_path, '-f', 'concat', '-safe', '0',
            '-i', concat_list.name,
            '-codec:a', 'libmp3lame', '-q:a', '2',
            '-y', output.name
        ]
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            raise Exception(f"FFmpeg merge error: {result.stderr}")
        return output.name

    def process_audio(
        self,
        input_path: str,
        output_path: str,
        settings: dict,
        cover_path: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        Обрабатывает аудио файл с применением всех указанных настроек

        Args:
            input_path: Путь к входному файлу
            output_path: Путь для выходного файла
            settings: Настройки обработки
            cover_path: Путь к файлу обложки (опционально)
            metadata: Метаданные для записи (опционально)

        Returns:
            Кортеж (success: bool, error_message: str)
        """
        temp_files = []
        current_input = input_path

        try:
            # Шаг 1: Обрезка тишины
            if settings['methods'].get('trim_silence', False):
                trim_dur = settings.get('trim_duration', 5)
                current_input = self.trim_silence(current_input, trim_dur)
                temp_files.append(current_input)

            # Шаг 2: Вырезание фрагмента
            if settings['methods'].get('cut_fragment', False):
                cut_pos = settings.get('cut_position_percent', 50)
                cut_dur = settings.get('cut_duration', 2)
                current_input = self.cut_fragment(current_input, cut_pos, cut_dur)
                temp_files.append(current_input)

            # Шаг 3: Сращивание с другим треком
            if settings['methods'].get('merge', False):
                extra_track = settings.get('extra_track_path', '')
                if extra_track and os.path.exists(extra_track):
                    current_input = self.merge_tracks(current_input, extra_track)
                    temp_files.append(current_input)

            # Построение фильтров
            filters = FilterBuilder.build_filters(settings)

            # Добавление fade out если нужно
            if settings['methods'].get('fade_out', False):
                fade_dur = settings.get('fade_duration', 5)
                duration = self.get_audio_duration(current_input)
                if duration > 0:
                    fade_start = max(0, duration - fade_dur)
                    if filters:
                        filters += f",afade=t=out:st={fade_start}:d={fade_dur}"
                    else:
                        filters = f"afade=t=out:st={fade_start}:d={fade_dur}"

            # Построение команды FFmpeg
            cmd = [self.ffmpeg_path, '-i', current_input]

            # Добавление обложки
            if cover_path and os.path.exists(cover_path):
                cmd.extend(['-i', cover_path, '-map', '0:a', '-map', '1:v'])
                cmd.extend([
                    '-c:v', 'mjpeg', '-q:v', '2',
                    '-disposition:v', 'attached_pic'
                ])
            else:
                cmd.extend(['-map', '0:a'])

            # Применение фильтров
            if filters:
                cmd.extend(['-af', filters])

            # Добавление метаданных
            if metadata:
                if metadata.get('title'):
                    cmd.extend(['-metadata', f"title={metadata['title']}"])
                if metadata.get('artist'):
                    cmd.extend(['-metadata', f"artist={metadata['artist']}"])
                if metadata.get('album'):
                    cmd.extend(['-metadata', f"album={metadata['album']}"])
                if metadata.get('year'):
                    cmd.extend(['-metadata', f"date={metadata['year']}"])
                if metadata.get('genre'):
                    cmd.extend(['-metadata', f"genre={metadata['genre']}"])

            # Фальшивые метаданные
            if settings['methods'].get('fake_metadata', False):
                fake_text = ''.join(random.choices(
                    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
                    k=random.randint(100, 500)
                ))
                cmd.extend(['-metadata', f'comment={fake_text}'])

            # Выбор битрейта
            if settings['methods'].get('bitrate_jitter', False):
                bitrate = random.choice([192, 224, 256, 320])
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', f'{bitrate}k'])
            else:
                quality = settings.get('quality', '2')
                cmd.extend(['-codec:a', 'libmp3lame', '-q:a', quality])

            # Отключение Xing заголовка (сдвиг фреймов)
            if settings['methods'].get('frame_shift', False) and \
               not settings['methods'].get('broken_duration', False):
                cmd.extend(['-write_xing', '0'])

            # Завершение команды
            cmd.extend(['-id3v2_version', '3', '-y', output_path])

            # Выполнение
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                return False, f"FFmpeg error: {result.stderr}"

            # Применение модификации длительности (broken duration)
            if settings['methods'].get('broken_duration', False):
                bug_type = settings.get('broken_type', 0)
                self._apply_broken_duration(output_path, bug_type)

            # Переупорядочивание ID3 тегов
            if settings['methods'].get('reorder_tags', False):
                self._reorder_id3_tags(output_path)

            return True, ""

        except Exception as e:
            return False, f"Processing error: {str(e)}"

        finally:
            # Очистка временных файлов
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass

    def _reorder_id3_tags(self, file_path: str):
        """Переупорядочивает ID3 теги"""
        try:
            audio = MP3(file_path)
            if audio.tags:
                audio.tags.update_to_v23()
                audio.save()
        except Exception as e:
            print(f"Error reordering tags: {e}")

    def _apply_broken_duration(self, file_path: str, bug_type: int):
        """
        Применяет модификацию длительности для сбоя парсинга

        Типы багов:
        0 - Классический (1:04:19)
        1 - Смещение +1 час
        2 - Смещение x15
        3 - Фейковый Xing
        """
        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())

            # Поиск VBR заголовка
            xing_pos = data.find(b'Xing')
            info_pos = data.find(b'Info')
            vbr_pos = xing_pos if xing_pos > 0 else info_pos

            if vbr_pos > 0 and vbr_pos < len(data) - 12:
                if bug_type == 0:  # Классический
                    fake_frames = 0x00186A00  # ~1:04:19
                    data[vbr_pos + 8:vbr_pos + 12] = fake_frames.to_bytes(4, 'big')

                elif bug_type == 1:  # +1 час
                    orig_frames = int.from_bytes(data[vbr_pos + 8:vbr_pos + 12], 'big')
                    fake_frames = orig_frames + 158760  # ~1 час
                    data[vbr_pos + 8:vbr_pos + 12] = fake_frames.to_bytes(4, 'big')

                elif bug_type == 2:  # x15
                    orig_frames = int.from_bytes(data[vbr_pos + 8:vbr_pos + 12], 'big')
                    fake_frames = orig_frames * 15
                    data[vbr_pos + 8:vbr_pos + 12] = fake_frames.to_bytes(4, 'big')

                elif bug_type == 3:  # Фейковый Xing
                    data[vbr_pos:vbr_pos + 4] = b'XXXX'
                    fake_frames = 0x0030D400
                    data[vbr_pos + 8:vbr_pos + 12] = fake_frames.to_bytes(4, 'big')

            with open(file_path, 'wb') as f:
                f.write(data)

            # Добавление TLEN тега
            audio = MP3(file_path)
            if audio.tags:
                fake_tlen = 3859000  # Фейковая длительность в миллисекундах
                audio.tags['TLEN'] = TLEN(encoding=3, text=str(fake_tlen))
                if bug_type == 3:
                    audio.tags['TXXX:BrokenVBR'] = TXXX(
                        encoding=3, desc='BrokenVBR', text='true'
                    )
                audio.save()

        except Exception as e:
            print(f"Error applying broken duration: {e}")

    def cleanup(self):
        """Очищает все временные файлы"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
        self.temp_files = []
