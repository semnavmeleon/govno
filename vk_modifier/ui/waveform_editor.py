"""Продвинутый waveform редактор в стиле FL Studio с drag-and-drop маркерами."""

import os
import struct
import subprocess
import logging
from typing import Optional, List, Tuple

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer, QThread
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient, QFont,
    QMouseEvent, QPaintEvent, QResizeEvent, QCursor,
)

from ..core.ffmpeg import find_ffmpeg, _STARTUPINFO, _CREATION_FLAGS

logger = logging.getLogger('vk_modifier.ui.waveform_editor')


class Marker:
    """Маркер для обрезки/вырезки."""
    
    TYPE_TRIM_START = 'trim_start'
    TYPE_CUT_START = 'cut_start'
    TYPE_CUT_END = 'cut_end'
    TYPE_PLAYHEAD = 'playhead'
    
    def __init__(self, marker_type: str, position_sec: float = 0.0, color: QColor = None):
        self.type = marker_type
        self.position_sec = position_sec
        self.color = color or QColor('#00ff88')
        self.dragging = False
        self.width = 4
        
    def get_color(self) -> QColor:
        if self.type == self.TYPE_TRIM_START:
            return QColor('#ff9800')  # Orange
        elif self.type == self.TYPE_CUT_START:
            return QColor('#ff5252')  # Red
        elif self.type == self.TYPE_CUT_END:
            return QColor('#ff5252')  # Red
        elif self.type == self.TYPE_PLAYHEAD:
            return QColor('#00bcd4')  # Cyan
        return self.color


class WaveformEditor(QFrame):
    """
    Waveform редактор в стиле FL Studio.
    - Отображение волны аудио
    - Drag-and-drop маркеры обрезки
    - Playhead для воспроизведения
    - Зум и панорамирование
    - Превью эффектов в реальном времени
    """
    
    position_changed = pyqtSignal(float)  # позиция playhead в секундах
    marker_moved = pyqtSignal(str, float)  # тип маркера, новая позиция
    region_selected = pyqtSignal(float, float)  # начало, конец выделенной области
    zoom_changed = pyqtSignal(float)  # уровень зума
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('waveformFrame')
        self.setFixedHeight(200)
        
        # Данные волны
        self._samples: List[float] = []
        self._duration: float = 0.0
        self._sample_rate: int = 44100
        self._channels: int = 2
        
        # Маркеры
        self._markers: List[Marker] = []
        self._playhead = Marker(Marker.TYPE_PLAYHEAD, 0.0)
        self._hover_marker: Optional[Marker] = None
        self._drag_marker: Optional[Marker] = None
        
        # Навигация
        self._zoom: float = 1.0
        self._zoom_min: float = 1.0
        self._zoom_max: float = 100.0
        self._scroll_offset: float = 0.0  # в секундах
        self._pixels_per_sec: float = 50.0
        
        # Состояние
        self._loading: bool = False
        self._has_data: bool = False
        self._mouse_x: int = 0
        self._is_mouse_down: bool = False
        self._selection_start: Optional[float] = None
        
        # Эффекты (для превью)
        self._effects_preview: dict = {}
        self._preview_modified: bool = False
        
        # Timer для плавного обновления
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)  # ~60 FPS
        self._update_timer.timeout.connect(self.update)
        
        self._setup_ui()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        
        # Верхняя панель с информацией
        self._info_label = QLabel("Нет аудиофайла")
        self._info_label.setStyleSheet("""
            QLabel {
                color: #909090;
                font-size: 11px;
                padding: 4px 8px;
                background: #1a1a1a;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        lay.addWidget(self._info_label)
        
    def load_audio(self, file_path: str):
        """Загрузить аудиофайл и отобразить волну."""
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            self._info_label.setText("❌ Файл не найден")
            return
            
        self._loading = True
        self._has_data = False
        self._samples = []
        self._update_timer.start()
        
        # Запуск в фоне
        from PyQt5.QtCore import QThread
        self._loader = WaveformLoaderThread(file_path)
        self._loader.loaded.connect(self._on_waveform_loaded)
        self._loader.error.connect(self._on_load_error)
        self._loader.start()
        
    def _on_waveform_loaded(self, samples: List[float], duration: float, 
                           sample_rate: int, channels: int):
        """Обработка загруженных данных волны."""
        self._samples = samples
        self._duration = duration
        self._sample_rate = sample_rate
        self._channels = channels
        self._loading = False
        self._has_data = True
        self._update_timer.stop()
        
        # Сброс маркеров
        self._markers.clear()
        self._playhead.position_sec = 0.0
        self._scroll_offset = 0.0
        self._zoom = 1.0
        
        # Обновление информации
        self._info_label.setText(
            f"🎵 {self._format_duration(duration)} · {sample_rate}Hz · {channels}ch"
        )
        
        self.update()
        
    def _on_load_error(self, error: str):
        """Обработка ошибки загрузки."""
        self._loading = False
        self._info_label.setText(f"❌ Ошибка: {error}")
        self.update()
        
    def set_markers(self, trim_start: float = 0.0, cut_start: float = 0.0, 
                   cut_end: float = 0.0):
        """Установить маркеры обрезки/вырезки."""
        self._markers.clear()
        
        if trim_start > 0:
            self._markers.append(Marker(Marker.TYPE_TRIM_START, trim_start))
            
        if cut_start > 0 and cut_end > cut_start:
            self._markers.append(Marker(Marker.TYPE_CUT_START, cut_start))
            self._markers.append(Marker(Marker.TYPE_CUT_END, cut_end))
            
        self.update()
        
    def set_playhead(self, position_sec: float):
        """Установить позицию playhead."""
        self._playhead.position_sec = max(0.0, min(position_sec, self._duration))
        self.update()
        
    def set_effects_preview(self, effects: dict):
        """Установить параметры эффектов для превью."""
        self._effects_preview = effects
        self._preview_modified = True
        # В будущем здесь будет перерисовка с учётом эффектов
        
    def get_visible_range(self) -> Tuple[float, float]:
        """Получить видимый диапазон времени (начало, конец)."""
        start = self._scroll_offset
        width_sec = self.width() / self._pixels_per_sec
        end = min(start + width_sec, self._duration)
        return (start, end)
        
    def _time_to_x(self, time_sec: float) -> float:
        """Преобразовать время в X координату."""
        return (time_sec - self._scroll_offset) * self._pixels_per_sec
        
    def _x_to_time(self, x: float) -> float:
        """Преобразовать X координату во время."""
        return self._scroll_offset + x / self._pixels_per_sec
        
    def _format_duration(self, seconds: float) -> str:
        """Форматировать длительность в MM:SS.mmm."""
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:06.3f}"
        
    def _format_time(self, seconds: float) -> str:
        """Форматировать время в MM:SS.mmm."""
        return self._format_duration(seconds)
        
    # ══════════════════════════════════════════════════════════════════════════
    #  СОБЫТИЯ МЫШИ
    # ══════════════════════════════════════════════════════════════════════════
    
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия мыши."""
        if not self._has_data:
            return
            
        self._mouse_x = event.x()
        self._is_mouse_down = True
        time_pos = self._x_to_time(event.x())
        
        # Проверка попадания в маркер
        for marker in self._markers + [self._playhead]:
            marker_x = self._time_to_x(marker.position_sec)
            if abs(event.x() - marker_x) < 10:
                self._drag_marker = marker
                marker.dragging = True
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                return
                
        # Клик по волне — перемещение playhead
        self._playhead.position_sec = max(0.0, min(time_pos, self._duration))
        self.position_changed.emit(self._playhead.position_sec)
        self.update()
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Обработка перемещения мыши."""
        if not self._has_data:
            return
            
        self._mouse_x = event.x()
        time_pos = self._x_to_time(event.x())
        
        # Drag маркера
        if self._drag_marker:
            new_pos = max(0.0, min(time_pos, self._duration))
            self._drag_marker.position_sec = new_pos
            self.marker_moved.emit(self._drag_marker.type, new_pos)
            self.update()
            return
            
        # Hover над маркером
        self._hover_marker = None
        for marker in self._markers + [self._playhead]:
            marker_x = self._time_to_x(marker.position_sec)
            if abs(event.x() - marker_x) < 10:
                self._hover_marker = marker
                self.setCursor(QCursor(Qt.OpenHandCursor))
                break
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
            
        self.update()
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Обработка отпускания мыши."""
        if self._drag_marker:
            self._drag_marker.dragging = False
            self._drag_marker = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            
        self._is_mouse_down = False
        self._selection_start = None
        
    def wheelEvent(self, event):
        """Обработка колёсика мыши для зума."""
        if not self._has_data:
            return
            
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        old_zoom = self._zoom
        self._zoom = max(self._zoom_min, min(self._zoom * zoom_factor, self._zoom_max))
        
        if self._zoom != old_zoom:
            self._pixels_per_sec = 50.0 * self._zoom
            self.zoom_changed.emit(self._zoom)
            self.update()
            
    # ══════════════════════════════════════════════════════════════════════════
    #  ОТРИСОВКА
    # ══════════════════════════════════════════════════════════════════════════
    
    def paintEvent(self, event: QPaintEvent):
        """Отрисовка waveform редактора."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Фон
        painter.fillRect(self.rect(), QColor('#0f0f0f'))
        
        if self._loading:
            self._draw_loading(painter)
            return
            
        if not self._has_data or not self._samples:
            self._draw_empty(painter)
            return
            
        # Сетка
        self._draw_grid(painter)
        
        # Волна
        self._draw_waveform(painter)
        
        # Маркеры
        self._draw_markers(painter)
        
        # Playhead
        self._draw_playhead(painter)
        
        # Шкала времени
        self._draw_time_ruler(painter)
        
    def _draw_loading(self, painter: QPainter):
        """Отрисовка состояния загрузки."""
        painter.setPen(QColor('#909090'))
        painter.setFont(QFont('Segoe UI', 12))
        painter.drawText(self.rect(), Qt.AlignCenter, "Загрузка волны...")
        
    def _draw_empty(self, painter: QPainter):
        """Отрисовка пустого состояния."""
        painter.setPen(QColor('#4a4a4a'))
        painter.setFont(QFont('Segoe UI', 12))
        painter.drawText(self.rect(), Qt.AlignCenter, "Перетащите аудиофайл или выберите в списке")
        
    def _draw_grid(self, painter: QPainter):
        """Отрисовка сетки."""
        painter.setPen(QPen(QColor('#1a1a1a'), 1))
        
        # Вертикальные линии по секундам
        start_sec, end_sec = self.get_visible_range()
        for sec in range(int(start_sec), int(end_sec) + 1):
            x = self._time_to_x(sec)
            if 0 <= x <= self.width():
                painter.drawLine(int(x), 0, int(x), self.height())
                
    def _draw_waveform(self, painter: QPainter):
        """Отрисовка волны аудио."""
        if not self._samples:
            return
            
        n_samples = len(self._samples)
        if n_samples == 0:
            return
            
        start_sec, end_sec = self.get_visible_range()
        start_sample = int(start_sec / self._duration * n_samples)
        end_sample = int(end_sec / self._duration * n_samples) + 1
        
        if start_sample >= end_sample:
            return
            
        visible_samples = self._samples[start_sample:end_sample]
        if not visible_samples:
            return
            
        # Градиент для волны
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor('#00ff88'))
        gradient.setColorAt(0.5, QColor('#00bcd4'))
        gradient.setColorAt(1, QColor('#00ff88'))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        
        # Отрисовка сэмплов
        w = self.width()
        h = self.height()
        mid = h / 2
        visible_range = end_sec - start_sec
        
        if visible_range <= 0:
            return
            
        samples_per_pixel = max(1, len(visible_samples) / w)
        max_sample = max(abs(s) for s in visible_samples) if visible_samples else 1.0
        if max_sample == 0:
            max_sample = 1.0
            
        for x in range(w):
            sample_start = int(x * samples_per_pixel)
            sample_end = int((x + 1) * samples_per_pixel)
            
            if sample_start >= len(visible_samples):
                break
                
            chunk = visible_samples[sample_start:sample_end]
            if not chunk:
                continue
                
            amp = max(abs(s) for s in chunk) / max_sample
            bar_h = max(1, int(amp * mid * 0.9))
            
            painter.drawRect(x, int(mid - bar_h), 1, bar_h * 2)
            
    def _draw_markers(self, painter: QPainter):
        """Отрисовка маркеров обрезки/вырезки."""
        for marker in self._markers:
            x = self._time_to_x(marker.position_sec)
            if x < -10 or x > self.width() + 10:
                continue
                
            color = marker.get_color()
            
            # Вертикальная линия
            painter.setPen(QPen(color, 2, Qt.DashLine))
            painter.drawLine(int(x), 0, int(x), self.height())
            
            # Треугольник сверху
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            triangle = [
                (int(x), 0),
                (int(x) - 6, 12),
                (int(x) + 6, 12),
            ]
            painter.drawPolygon([QPointF(*p) for p in triangle])
            
            # Подпись
            painter.setPen(QColor('#e0e0e0'))
            painter.setFont(QFont('Segoe UI', 9))
            label = f"{marker.position_sec:.2f}s"
            painter.drawText(int(x) + 8, 16, label)
            
    def _draw_playhead(self, painter: QPainter):
        """Отрисовка playhead."""
        x = self._time_to_x(self._playhead.position_sec)
        if x < -10 or x > self.width() + 10:
            return
            
        color = self._playhead.get_color()
        
        # Вертикальная линия
        painter.setPen(QPen(color, 2))
        painter.drawLine(int(x), 0, int(x), self.height())
        
        # Треугольник сверху
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        triangle = [
            (int(x), 0),
            (int(x) - 8, 16),
            (int(x) + 8, 16),
        ]
        painter.drawPolygon([QPointF(*p) for p in triangle])
        
        # Время
        painter.setPen(QColor('#00bcd4'))
        painter.setFont(QFont('Consolas', 10, QFont.Bold))
        time_str = self._format_time(self._playhead.position_sec)
        painter.drawText(int(x) + 10, self.height() - 8, time_str)
        
    def _draw_time_ruler(self, painter: QPainter):
        """Отрисовка шкалы времени."""
        h = self.height()
        start_sec, end_sec = self.get_visible_range()
        
        painter.setPen(QPen(QColor('#3a3a3a'), 1))
        painter.drawLine(0, h - 20, self.width(), h - 20)
        
        # Метки времени
        painter.setPen(QColor('#606060'))
        painter.setFont(QFont('Consolas', 9))
        
        step = 1.0  # секунда
        if self._zoom < 0.5:
            step = 5.0
        elif self._zoom > 5:
            step = 0.5
            
        for sec in range(int(start_sec), int(end_sec) + 1):
            if sec % int(step) != 0:
                continue
            x = self._time_to_x(sec)
            if 0 <= x <= self.width():
                painter.drawLine(int(x), h - 20, int(x), h - 15)
                painter.drawText(int(x) - 20, h - 5, 40, 15, Qt.AlignCenter, f"{sec}s")


class WaveformLoaderThread(QThread):
    """Фоновая загрузка данных волны."""
    
    loaded = pyqtSignal(list, float, int, int)  # samples, duration, sample_rate, channels
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            ffmpeg = find_ffmpeg() or 'ffmpeg'
            
            # Получение информации о файле
            probe_cmd = [
                ffmpeg, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', self.file_path,
            ]
            proc = subprocess.Popen(
                probe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            import json
            probe_data = json.loads(proc.communicate()[0])
            
            # Извлечение параметров
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
                    
            if not audio_stream:
                self.error.emit("Аудиопоток не найден")
                return
                
            sample_rate = int(audio_stream.get('sample_rate', 44100))
            channels = int(audio_stream.get('channels', 2))
            duration = float(probe_data.get('format', {}).get('duration', 0))
            
            # Извлечение PCM данных
            pcm_cmd = [
                ffmpeg, '-i', self.file_path,
                '-f', 'f32le', '-ac', '1', '-ar', '8000',
                '-',
            ]
            proc = subprocess.Popen(
                pcm_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            
            # Чтение данных (макс 10 минут)
            max_samples = 8000 * 600
            raw = proc.stdout.read(max_samples * 4)
            proc.wait()
            
            if not raw:
                self.error.emit("Не удалось извлечь аудио")
                return
                
            # Преобразование в float
            n_samples = len(raw) // 4
            samples = list(struct.unpack(f'{n_samples}f', raw[:n_samples * 4]))
            
            # Даунсемплинг для отображения
            target_samples = 10000
            if n_samples > target_samples:
                step = n_samples // target_samples
                downsampled = []
                for i in range(0, n_samples - step, step):
                    chunk = samples[i:i + step]
                    downsampled.append(max(abs(s) for s in chunk))
                samples = downsampled
                
            self.loaded.emit(samples, duration, sample_rate, channels)
            
        except Exception as e:
            logger.error(f"Waveform load error: {e}")
            self.error.emit(str(e))
