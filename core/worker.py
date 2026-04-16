"""Многопоточная обработка файлов с отменой, паузой и по-шаговым прогрессом."""

import os
import random
import tempfile
import logging

from PyQt5.QtCore import QObject, QThread, QRunnable, QThreadPool, pyqtSignal, QMutex, QWaitCondition

from mutagen.mp3 import MP3
from mutagen.id3 import TLEN, TXXX

from .ffmpeg import run_ffmpeg
from .filters import FilterChain, get_codec_args
from .branding import BrandingEngine

logger = logging.getLogger('vk_modifier.worker')


class FileTask(QRunnable):
    """Обработка одного файла в пуле потоков."""

    class Signals(QObject):
        step_changed = pyqtSignal(str, int, int, str)   # file_path, step, total_steps, step_name
        file_complete = pyqtSignal(str, bool, str, str)  # file_path, success, output_path, error_msg
        log_message = pyqtSignal(str, str)               # level, message

    def __init__(self, file_path, track_info, index, output_dir, settings):
        super().__init__()
        self.file_path = file_path
        self.track_info = track_info
        self.index = index
        self.output_dir = output_dir
        self.settings = settings
        self.signals = self.Signals()
        self.cancelled = False
        self.setAutoDelete(True)

        # Пауза
        self._pause_mutex = QMutex()
        self._pause_cond = QWaitCondition()
        self._paused = False

    def cancel(self):
        self.cancelled = True

    def pause(self):
        self._pause_mutex.lock()
        self._paused = True
        self._pause_mutex.unlock()

    def resume(self):
        self._pause_mutex.lock()
        self._paused = False
        self._pause_cond.wakeAll()
        self._pause_mutex.unlock()

    def _check_pause_cancel(self) -> bool:
        """Проверить паузу/отмену. Возвращает True если отменено."""
        if self.cancelled:
            return True
        self._pause_mutex.lock()
        while self._paused and not self.cancelled:
            self._pause_cond.wait(self._pause_mutex)
        self._pause_mutex.unlock()
        return self.cancelled

    def _emit_step(self, step: int, total: int, name: str):
        self.signals.step_changed.emit(self.file_path, step, total, name)

    def run(self):
        temp_files = []
        try:
            branding = BrandingEngine(self.settings)

            # Определить количество шагов
            steps = self._count_steps()
            current_step = 0

            current_input = self.file_path
            current_duration = self.track_info.duration_sec

            # ── Шаг: Обрезка начала ──
            trim = self.settings.get('trim_start_sec', 0)
            if trim > 0:
                current_step += 1
                self._emit_step(current_step, steps, "Обрезка начала")
                if self._check_pause_cancel():
                    return self._cancelled_result()

                tmp = self._make_temp()
                temp_files.append(tmp)
                r = run_ffmpeg(['-i', current_input, '-ss', str(trim),
                                '-codec:a', 'copy', '-y', tmp])
                if r.returncode == 0:
                    current_input = tmp
                    current_duration = max(0, current_duration - trim)

            # ── Шаг: Вырезка фрагмента ──
            cut_start = self.settings.get('cut_start_sec', 0.0)
            cut_end = self.settings.get('cut_end_sec', 0.0)
            if cut_start > 0 and cut_end > cut_start and current_duration > (cut_end - cut_start) + 1:
                current_step += 1
                self._emit_step(current_step, steps, "Вырезка фрагмента")
                if self._check_pause_cancel():
                    return self._cancelled_result()

                tmp = self._make_temp()
                temp_files.append(tmp)
                fc = (f"[0:a]atrim=0:{cut_start:.3f},asetpts=PTS-STARTPTS[a];"
                      f"[0:a]atrim={cut_end:.3f},asetpts=PTS-STARTPTS[b];"
                      f"[a][b]concat=n=2:v=0:a=1[out]")
                r = run_ffmpeg(['-i', current_input, '-filter_complex', fc,
                                '-map', '[out]', '-codec:a', 'libmp3lame', '-q:a', '2', '-y', tmp])
                if r.returncode == 0:
                    current_input = tmp
                    current_duration -= (cut_end - cut_start)

            # ── Шаг: Сращивание ──
            if self.settings.get('merge_enabled') and self.settings.get('merge_track_path'):
                current_step += 1
                self._emit_step(current_step, steps, "Сращивание")
                if self._check_pause_cancel():
                    return self._cancelled_result()

                tmp = self._make_temp()
                temp_files.append(tmp)
                quality = self.settings.get('quality', '2')
                r = run_ffmpeg([
                    '-i', current_input, '-i', self.settings['merge_track_path'],
                    '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1[out]',
                    '-map', '[out]', '-codec:a', 'libmp3lame', '-q:a', quality, '-y', tmp
                ])
                if r.returncode == 0:
                    current_input = tmp

            # ── Шаг: Основная обработка ──
            current_step += 1
            self._emit_step(current_step, steps, "Кодирование и эффекты")
            if self._check_pause_cancel():
                return self._cancelled_result()

            # Имя выходного файла
            output_name = branding.render_filename(self.track_info, self.index)
            output_file = os.path.join(self.output_dir, output_name)

            # Фильтры
            chain = FilterChain(self.settings, current_duration)
            _, filter_str, map_label = chain.build()

            cmd = ['-i', current_input]

            # Обложка
            cover_temp = None
            cover_data, cover_mime = self._get_cover()
            if cover_data:
                ext = 'png' if (cover_mime and 'png' in cover_mime) else 'jpg'
                cover_temp = self._make_temp(f'.{ext}')
                temp_files.append(cover_temp)
                with open(cover_temp, 'wb') as f:
                    f.write(cover_data)

            # Собрать команду
            if map_label:
                # filter_complex
                cmd.extend(['-filter_complex', filter_str, '-map', map_label])
                if cover_temp:
                    cmd.extend(['-i', cover_temp, '-map', '1:v',
                                '-c:v', 'copy', '-disposition:v', 'attached_pic'])
            elif filter_str:
                # простой -af
                if cover_temp:
                    cmd.extend(['-i', cover_temp, '-map', '0:a', '-map', '1:v',
                                '-c:v', 'copy', '-disposition:v', 'attached_pic'])
                else:
                    cmd.extend(['-map', '0:a'])
                cmd.extend(['-af', filter_str])
            else:
                # без фильтров
                if cover_temp:
                    cmd.extend(['-i', cover_temp, '-map', '0:a', '-map', '1:v',
                                '-c:v', 'copy', '-disposition:v', 'attached_pic'])
                else:
                    cmd.extend(['-map', '0:a'])

            # Метаданные
            cmd.extend(branding.get_metadata_args(self.track_info))

            # Кодек
            cmd.extend(get_codec_args(self.settings))
            cmd.extend(['-y', output_file])

            result = run_ffmpeg(cmd)

            # ── Пост-обработка ──
            if result.returncode == 0 and os.path.exists(output_file):
                if self.settings.get('reorder_tags'):
                    self._reorder_id3_tags(output_file)
                if self.settings.get('broken_duration_enabled'):
                    self._apply_broken_duration(
                        output_file, self.settings.get('broken_duration_type', 0)
                    )

                # Удалить оригинал если нужно
                if self.settings.get('delete_originals'):
                    try:
                        os.unlink(self.file_path)
                    except Exception:
                        pass

                self.signals.file_complete.emit(self.file_path, True, output_file, "")
            else:
                err = result.stderr[:500] if result.stderr else "Unknown error"
                self.signals.file_complete.emit(self.file_path, False, "", err)

        except Exception as e:
            logger.error(f"Task error {self.file_path}: {e}", exc_info=True)
            self.signals.file_complete.emit(self.file_path, False, "", str(e))
        finally:
            for tf in temp_files:
                try:
                    os.unlink(tf)
                except Exception:
                    pass

    def _cancelled_result(self):
        self.signals.file_complete.emit(self.file_path, False, "", "Отменено")

    def _count_steps(self) -> int:
        n = 1  # основная обработка всегда
        if self.settings.get('trim_start_sec', 0) > 0:
            n += 1
        if self.settings.get('cut_start_sec', 0) > 0 and self.settings.get('cut_end_sec', 0) > 0:
            n += 1
        if self.settings.get('merge_enabled') and self.settings.get('merge_track_path'):
            n += 1
        return n

    def _get_cover(self) -> tuple[bytes | None, str]:
        """Определить обложку по режиму."""
        mode = self.settings.get('cover_mode', 'original')

        if mode == 'remove':
            return None, ''
        if mode == 'single':
            # Одна обложка для всех — путь в настройках
            path = self.settings.get('cover_path', '')
            if path and os.path.isfile(path):
                with open(path, 'rb') as f:
                    data = f.read()
                mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
                return BrandingEngine.resize_cover(data), mime
        if mode == 'random':
            return self._generate_random_cover(), 'image/jpeg'

        # original: из трека
        data, mime = self.track_info.get_effective_cover()
        if data and self.settings.get('preserve_cover', True):
            return BrandingEngine.resize_cover(data), mime
        return None, ''

    def _generate_random_cover(self) -> bytes:
        """Сгенерировать обложку — градиент с текстом."""
        from PyQt5.QtGui import QPixmap, QColor, QPainter, QLinearGradient, QFont
        from PyQt5.QtCore import Qt, QBuffer, QIODevice, QPointF

        size = 500
        pixmap = QPixmap(size, size)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        c1 = QColor(random.randint(30, 180), random.randint(30, 180), random.randint(30, 180))
        c2 = QColor(random.randint(30, 180), random.randint(30, 180), random.randint(30, 180))
        grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        painter.fillRect(0, 0, size, size, grad)

        if self.track_info.title or self.track_info.artist:
            painter.setPen(QColor(255, 255, 255, 200))
            font = QFont("Segoe UI", 20, QFont.Bold)
            painter.setFont(font)
            text = self.track_info.artist or ''
            if text and self.track_info.title:
                text += '\n'
            text += self.track_info.title or ''
            painter.drawText(pixmap.rect().adjusted(30, 30, -30, -30),
                             Qt.AlignCenter | Qt.TextWordWrap, text)

        painter.end()

        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, 'JPEG', 90)
        return bytes(buf.data())

    @staticmethod
    def _make_temp(suffix='.mp3') -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.close()
        return tmp.name

    @staticmethod
    def _reorder_id3_tags(fp):
        try:
            audio = MP3(fp)
            if audio.tags:
                audio.tags.update_to_v23()
                k = ''.join(random.choices('ABCDEFGHIJKLMNOP', k=6))
                audio.tags[f'TXXX:{k}'] = TXXX(encoding=3, desc=k,
                                                 text=str(random.randint(1000, 9999)))
                audio.save()
        except Exception:
            pass

    @staticmethod
    def _apply_broken_duration(fp, bug_type):
        try:
            with open(fp, 'rb') as f:
                data = bytearray(f.read())
            xing = data.find(b'Xing')
            info = data.find(b'Info')
            pos = xing if xing > 0 else info
            if pos > 0 and pos + 12 <= len(data):
                flags = int.from_bytes(data[pos + 4:pos + 8], 'big')
                if not (flags & 0x01):
                    return
                if bug_type == 0:
                    data[pos + 8:pos + 12] = (0x00186A00).to_bytes(4, 'big')
                elif bug_type == 1:
                    orig = int.from_bytes(data[pos + 8:pos + 12], 'big')
                    data[pos + 8:pos + 12] = (orig + 158760).to_bytes(4, 'big')
                elif bug_type == 2:
                    orig = int.from_bytes(data[pos + 8:pos + 12], 'big')
                    data[pos + 8:pos + 12] = (orig * 15).to_bytes(4, 'big')
                elif bug_type == 3:
                    data[pos:pos + 4] = b'XXXX'
                    data[pos + 8:pos + 12] = (0x0030D400).to_bytes(4, 'big')
                with open(fp, 'wb') as f:
                    f.write(data)

            audio = MP3(fp)
            if audio.tags is None:
                audio.add_tags()
            audio.tags['TLEN'] = TLEN(encoding=3, text=str(3859000))
            if bug_type == 3:
                audio.tags['TXXX:BrokenVBR'] = TXXX(encoding=3, desc='BrokenVBR', text='true')
            audio.save()
        except Exception as e:
            logger.warning(f"Broken duration error: {e}")


class ProcessingPool(QObject):
    """Пул обработки с управлением потоками."""

    file_started = pyqtSignal(str)
    file_step = pyqtSignal(str, int, int, str)    # file, step, total, name
    file_complete = pyqtSignal(str, bool, str, str)  # file, ok, output, error
    all_complete = pyqtSignal(int, int)            # success_count, total

    def __init__(self, max_workers: int = 2):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(max_workers)
        self._tasks: list[FileTask] = []
        self._total = 0
        self._done = 0
        self._success = 0
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self, files, tracks_info, output_dir, settings):
        """Запустить обработку списка файлов."""
        self._tasks.clear()
        self._total = len(files)
        self._done = 0
        self._success = 0
        self._active = True

        for i, (fp, ti) in enumerate(zip(files, tracks_info)):
            task = FileTask(fp, ti, i, output_dir, settings)
            task.signals.step_changed.connect(self.file_step.emit)
            task.signals.file_complete.connect(self._on_task_done)
            self._tasks.append(task)
            self.pool.start(task)

    def _on_task_done(self, file_path, success, output, error):
        self._done += 1
        if success:
            self._success += 1
        self.file_complete.emit(file_path, success, output, error)

        if self._done >= self._total:
            self._active = False
            self.all_complete.emit(self._success, self._total)

    def cancel(self):
        """Отменить все задачи."""
        for task in self._tasks:
            task.cancel()
        self.pool.clear()
        self._active = False

    def pause(self):
        for task in self._tasks:
            task.pause()

    def resume(self):
        for task in self._tasks:
            task.resume()
