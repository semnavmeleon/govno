"""Waveform виджет для отображения аудио."""

import os
import struct
import subprocess
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QFont

from ..core.ffmpeg import find_ffmpeg, _STARTUPINFO, _CREATION_FLAGS

logger = logging.getLogger('vk_modifier.ui.waveform_widget')


class WaveformLoader(QThread):
    """Загрузка волны в фоне."""
    loaded = pyqtSignal(list, float)
    error = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            ffmpeg = find_ffmpeg() or 'ffmpeg'
            
            # Извлекаем PCM данные
            proc = subprocess.Popen(
                [ffmpeg, '-i', self.file_path, '-f', 'f32le', '-ac', '1', '-ar', '8000', '-'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            
            raw = proc.stdout.read(8000 * 60 * 4)  # Макс 60 секунд
            proc.wait()
            
            if not raw:
                self.error.emit("Не удалось извлечь аудио")
                return
                
            # Преобразуем в float
            n_samples = len(raw) // 4
            samples = list(struct.unpack(f'{n_samples}f', raw[:n_samples * 4]))
            
            # Даунсемплинг до 2000 точек
            target = 2000
            if len(samples) > target:
                step = len(samples) // target
                downsampled = []
                for i in range(0, len(samples) - step, step):
                    chunk = samples[i:i + step]
                    downsampled.append(max(abs(s) for s in chunk))
                samples = downsampled
                
            duration = len(samples) / 8000.0
            self.loaded.emit(samples, duration)
            
        except Exception as e:
            logger.error(f"Waveform load error: {e}")
            self.error.emit(str(e))


class WaveformWidget(QWidget):
    """Виджет волны аудио."""
    
    position_changed = pyqtSignal(float)
    marker_changed = pyqtSignal(str, float)
    
    def __init__(self):
        super().__init__()
        self.setObjectName('waveformFrame')
        
        self._samples = []
        self._duration = 0.0
        self._position = 0.0
        self._trim = 0.0
        self._cut_start = 0.0
        self._cut_end = 0.0
        self._dragging = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Инфо
        self.info_label = QLabel("Нет аудио")
        self.info_label.setStyleSheet("color: #606060; font-size: 11px; padding: 5px;")
        layout.addWidget(self.info_label)
        
        self.setMinimumHeight(180)
        
    def load_audio(self, file_path):
        """Загрузить аудиофайл."""
        if not os.path.exists(file_path):
            self.info_label.setText("❌ Файл не найден")
            return
            
        self._loader = WaveformLoader(file_path)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.error.connect(self._on_error)
        self._loader.start()
        
    def _on_loaded(self, samples, duration):
        self._samples = samples
        self._duration = duration
        self.info_label.setText(f"🎵 {self._format_time(duration)}")
        self.update()
        
    def _on_error(self, error):
        self.info_label.setText(f"❌ {error}")
        
    def set_markers(self, trim, cut_start, cut_end):
        """Установить маркеры."""
        self._trim = trim
        self._cut_start = cut_start
        self._cut_end = cut_end
        self.update()
        
    def set_position(self, position):
        """Установить позицию воспроизведения."""
        self._position = position
        self.update()
        
    def _format_time(self, seconds):
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:05.2f}"
        
    def _time_to_x(self, time_sec):
        if self._duration <= 0:
            return 0
        return (time_sec / self._duration) * self.width()
        
    def _x_to_time(self, x):
        if self._duration <= 0:
            return 0
        return (x / self.width()) * self._duration
        
    def mousePressEvent(self, event):
        x = event.x()
        time = self._x_to_time(x)
        self._position = time
        self.position_changed.emit(time)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Фон
        painter.fillRect(0, 0, w, h, QColor('#1a1a2e'))
        
        if not self._samples:
            painter.setPen(QColor('#606060'))
            painter.setFont(QFont('Segoe UI', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Загрузите аудиофайл")
            return
            
        # Рисуем волну
        self._draw_waveform(painter, w, h)
        
        # Рисуем маркеры
        self._draw_markers(painter, w, h)
        
        # Рисуем позицию
        self._draw_position(painter, w, h)
        
    def _draw_waveform(self, painter, w, h):
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor('#00adb5'))
        gradient.setColorAt(0.5, QColor('#e94560'))
        gradient.setColorAt(1, QColor('#00adb5'))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        
        mid = h / 2
        max_sample = max(self._samples) if self._samples else 1
        
        bar_w = w / len(self._samples)
        for i, sample in enumerate(self._samples):
            x = int(i * bar_w)
            amp = abs(sample) / max_sample
            bar_h = max(1, int(amp * mid * 0.9))
            painter.drawRect(x, int(mid - bar_h), int(bar_w), bar_h * 2)
            
    def _draw_markers(self, painter, w, h):
        # Trim маркер
        if self._trim > 0:
            x = int(self._time_to_x(self._trim))
            painter.setPen(QPen(QColor('#ffaa00'), 2, Qt.DashLine))
            painter.drawLine(x, 0, x, h)
            
            # Треугольник
            painter.setBrush(QBrush(QColor('#ffaa00')))
            painter.drawPolygon([
                (x, 0), (x - 6, 12), (x + 6, 12)
            ])
            
        # Cut маркеры
        if self._cut_start > 0:
            x = int(self._time_to_x(self._cut_start))
            painter.setPen(QPen(QColor('#ff4757'), 2, Qt.DashLine))
            painter.drawLine(x, 0, x, h)
            
        if self._cut_end > 0:
            x = int(self._time_to_x(self._cut_end))
            painter.setPen(QPen(QColor('#ff4757'), 2, Qt.DashLine))
            painter.drawLine(x, 0, x, h)
            
    def _draw_position(self, painter, w, h):
        x = int(self._time_to_x(self._position))
        painter.setPen(QPen(QColor('#00ff88'), 2))
        painter.drawLine(x, 0, x, h)
        
        # Время
        painter.setPen(QColor('#00ff88'))
        painter.setFont(QFont('Consolas', 10, QFont.Bold))
        painter.drawText(x + 10, h - 10, self._format_time(self._position))
