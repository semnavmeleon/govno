"""
Модуль процессоров для обработки аудио
Исправленная версия с качественными фильтрами и валидацией
"""

import os
import random
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple, Dict, Any

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TLEN, TXXX


# Предопределенные конфигурации (пресеты)
PRESETS = {
    "safe": {
        "name": "Безопасный",
        "description": "Минимальная обработка, сохранение качества",
        "settings": {
            "volume": 0.0,
            "normalize": True,
            "target_loudness": -14.0,
            "compress": False,
            "bass_gain": 0.0,
            "treble_gain": 0.0,
            "speed": 1.0,
            "pitch": 0.0,
            "fade_in": 0.0,
            "fade_out": 0.0
        }
    },
    "loud": {
        "name": "Громкий",
        "description": "Максимальная громкость для VK",
        "settings": {
            "volume": 3.0,
            "normalize": True,
            "target_loudness": -11.0,
            "compress": True,
            "compress_threshold": -15.0,
            "compress_ratio": 3.0,
            "compress_attack": 10.0,
            "compress_release": 80.0,
            "bass_gain": 2.0,
            "treble_gain": 1.5,
            "speed": 1.0,
            "pitch": 0.0,
            "fade_in": 0.5,
            "fade_out": 2.0
        }
    },
    "spatial": {
        "name": "Пространственный",
        "description": "Улучшение стерео и частот",
        "settings": {
            "volume": 0.0,
            "normalize": True,
            "target_loudness": -14.0,
            "compress": True,
            "compress_threshold": -20.0,
            "compress_ratio": 2.5,
            "compress_attack": 20.0,
            "compress_release": 100.0,
            "bass_gain": 3.0,
            "bass_freq": 80.0,
            "treble_gain": 2.0,
            "treble_freq": 12000.0,
            "speed": 1.0,
            "pitch": 0.0,
            "fade_in": 0.0,
            "fade_out": 1.0
        }
    },
    "transform": {
        "name": "Трансформация",
        "description": "Изменение скорости и тональности",
        "settings": {
            "volume": 0.0,
            "normalize": True,
            "target_loudness": -14.0,
            "compress": False,
            "speed": 1.05,
            "pitch": 0.0,
            "fade_in": 0.0,
            "fade_out": 1.0
        }
    }
}


class FilterBuilder:
    """Класс для построения FFmpeg аудио фильтров высокого качества"""

    @staticmethod
    def validate_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверяет совместимость настроек
        
        Returns:
            (is_valid, error_message)
        """
        errors = []
        
        # Проверка диапазонов
        if not (-50 <= settings.get('volume', 0) <= 20):
            errors.append("Volume должен быть от -50 до 20 dB")
        
        if not (-24 <= settings.get('target_loudness', -14) <= -10):
            errors.append("Target Loudness должен быть от -24 до -10 LUFS")
        
        if not (0.5 <= settings.get('speed', 1.0) <= 2.0):
            errors.append("Speed должен быть от 0.5 до 2.0")
        
        if not (-12 <= settings.get('pitch', 0) <= 12):
            errors.append("Pitch должен быть от -12 до 12 полутонов")
        
        # Проверка несовместимых комбинаций
        if settings.get('normalize') and settings.get('volume', 0) > 10:
            errors.append("Нормализация и Volume > 10dB могут вызвать клиппинг")
        
        if settings.get('compress') and settings.get('compress_ratio', 4) > 10:
            errors.append("Компрессия с ratio > 10 вызывает сильные артефакты")
        
        # Pitch и Speed вместе требуют особого подхода
        if abs(settings.get('pitch', 0)) > 6 and abs(settings.get('speed', 1.0) - 1.0) > 0.2:
            errors.append("Сильное изменение pitch и speed одновременно ухудшает качество")
        
        return (len(errors) == 0, "; ".join(errors))

    @staticmethod
    def build_filters(settings: Dict[str, Any]) -> Optional[str]:
        """
        Строит строку аудио фильтров для FFmpeg на основе настроек
        Использует качественные алгоритмы вместо asetrate/aresample

        Args:
            settings: Словарь с настройками обработки

        Returns:
            Строка фильтров или None если фильтры не нужны
        """
        filters = []
        
        # 1. Эквализация (первой для чистоты сигнала)
        if settings.get('bass_gain', 0) != 0 or settings.get('treble_gain', 0) != 0:
            bass_gain = settings.get('bass_gain', 0)
            bass_freq = settings.get('bass_freq', 100)
            treble_gain = settings.get('treble_gain', 0)
            treble_freq = settings.get('treble_freq', 10000)
            
            if bass_gain != 0:
                filters.append(f"bass=g={bass_gain}:f={bass_freq}:width=0.5")
            if treble_gain != 0:
                filters.append(f"treble=g={treble_gain}:f={treble_freq}:width=0.5")
        
        # 2. Компрессия (если включена)
        if settings.get('compress', False):
            threshold = settings.get('compress_threshold', -20)
            ratio = settings.get('compress_ratio', 4)
            attack = settings.get('compress_attack', 20) / 1000  # ms -> seconds
            release = settings.get('compress_release', 100) / 1000  # ms -> seconds
            
            # Мягкая компрессия для избежания артефактов
            filters.append(
                f"compander=attacks={attack}:{release}:"
                f"points=-80/-80|{threshold}/{threshold}|0/{threshold + (0 - threshold) / ratio}:"
                f"soft-knee=3dB:threshold={threshold}:ratio={ratio}"
            )
        
        # 3. Нормализация (после компрессии)
        if settings.get('normalize', False):
            target = settings.get('target_loudness', -14)
            filters.append(f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=summary")
        
        # 4. Регулировка громкости (последней перед pitch/speed)
        if settings.get('volume', 0) != 0:
            vol = settings.get('volume', 0)
            filters.append(f"volume={vol}dB")
        
        # 5. Изменение скорости и тональности
        # ИСПРАВЛЕНО: Используем rubberband вместо asetrate/aresample для сохранения качества
        speed = settings.get('speed', 1.0)
        pitch = settings.get('pitch', 0.0)
        
        if speed != 1.0 or pitch != 0.0:
            # rubberband фильтр обеспечивает высокое качество
            # pitch в полутонах конвертиется в множитель: 2^(semitones/12)
            if pitch != 0.0:
                pitch_multiplier = 2 ** (pitch / 12)
            else:
                pitch_multiplier = 1.0
            
            # Для rubberband: tempo для скорости, pitch для тональности
            if speed != 1.0 and pitch == 0.0:
                # Только скорость
                filters.append(f"rubberband=tempo={speed}")
            elif speed == 1.0 and pitch != 0.0:
                # Только тональность
                filters.append(f"rubberband=pitch={pitch_multiplier}")
            else:
                # И то и другое
                filters.append(f"rubberband=tempo={speed}:pitch={pitch_multiplier}")
        
        # 6. Fade эффекты
        fade_in = settings.get('fade_in', 0)
        fade_out = settings.get('fade_out', 0)
        
        if fade_in > 0 or fade_out > 0:
            # Fade добавляется отдельно через afade
            pass  # Обработано в process_audio
        
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
        Использует новый формат настроек (ProcessingSettings)

        Args:
            input_path: Путь к входному файлу
            output_path: Путь для выходного файла
            settings: Настройки обработки (словарь из ProcessingSettings.to_dict())
            cover_path: Путь к файлу обложки (опционально)
            metadata: Метаданные для записи (опционально)

        Returns:
            Кортеж (success: bool, error_message: str)
        """
        temp_files = []
        current_input = input_path

        try:
            # Валидация настроек
            is_valid, error_msg = FilterBuilder.validate_settings(settings)
            if not is_valid:
                return False, f"Validation error: {error_msg}"

            # Шаг 1: Обрезка тишины (если есть в старом формате)
            if settings.get('methods', {}).get('trim_silence', False):
                trim_dur = settings.get('trim_duration', 5)
                current_input = self.trim_silence(current_input, trim_dur)
                temp_files.append(current_input)

            # Шаг 2: Вырезание фрагмента (если есть в старом формате)
            if settings.get('methods', {}).get('cut_fragment', False):
                cut_pos = settings.get('cut_position_percent', 50)
                cut_dur = settings.get('cut_duration', 2)
                current_input = self.cut_fragment(current_input, cut_pos, cut_dur)
                temp_files.append(current_input)

            # Шаг 3: Сращивание с другим треком (если есть в старом формате)
            if settings.get('methods', {}).get('merge', False):
                extra_track = settings.get('extra_track_path', '')
                if extra_track and os.path.exists(extra_track):
                    current_input = self.merge_tracks(current_input, extra_track)
                    temp_files.append(current_input)

            # Построение фильтров на основе новых настроек
            filters = FilterBuilder.build_filters(settings)

            # Добавление fade in/out если нужно
            fade_in = settings.get('fade_in', 0)
            fade_out = settings.get('fade_out', 0)
            
            if fade_in > 0 or fade_out > 0:
                duration = self.get_audio_duration(current_input)
                if duration > 0:
                    fade_parts = []
                    if fade_in > 0:
                        fade_parts.append(f"afade=t=in:st=0:d={fade_in}")
                    if fade_out > 0:
                        fade_start = max(0, duration - fade_out)
                        fade_parts.append(f"afade=t=out:st={fade_start}:d={fade_out}")
                    
                    if filters:
                        filters += "," + ",".join(fade_parts)
                    else:
                        filters = ",".join(fade_parts)

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

            # Фальшивые метаданные (старый функционал)
            if settings.get('methods', {}).get('fake_metadata', False):
                fake_text = ''.join(random.choices(
                    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
                    k=random.randint(100, 500)
                ))
                cmd.extend(['-metadata', f'comment={fake_text}'])

            # Выбор битрейта
            if settings.get('methods', {}).get('bitrate_jitter', False):
                bitrate = random.choice([192, 224, 256, 320])
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', f'{bitrate}k'])
            else:
                quality = settings.get('quality', '2')
                cmd.extend(['-codec:a', 'libmp3lame', '-q:a', quality])

            # Отключение Xing заголовка (сдвиг фреймов)
            if settings.get('methods', {}).get('frame_shift', False) and \
               not settings.get('methods', {}).get('broken_duration', False):
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
            if settings.get('methods', {}).get('broken_duration', False):
                bug_type = settings.get('broken_type', 0)
                self._apply_broken_duration(output_path, bug_type)

            # Переупорядочивание ID3 тегов
            if settings.get('methods', {}).get('reorder_tags', False):
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
