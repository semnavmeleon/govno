"""Транспортная панель в стиле FL Studio с аудиоплеером и визуализацией."""

import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, 
    QPushButton, QSlider, QProgressBar, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class TransportButton(QPushButton):
    """Кнопка транспорта в стиле FL Studio."""
    
    def __init__(self, icon: str, tooltip: str = '', parent=None):
        super().__init__(icon, parent)
        self.setCheckable(False)
        self.setFixedSize(44, 44)
        self.setToolTip(tooltip)
        self.setObjectName('transportBtn')
        self.setStyleSheet("""
            QPushButton#transportBtn {
                background: #1a1a1a;
                border: 2px solid #3a3a3a;
                border-radius: 22px;
                color: #909090;
                font-size: 18px;
            }
            QPushButton#transportBtn:hover {
                border-color: #00ff88;
                color: #00ff88;
                background: #242424;
            }
            QPushButton#transportBtn:pressed {
                background: #0f0f0f;
            }
        """)


class LevelMeter(QFrame):
    """Визуализатор уровня аудио в стиле FL Studio."""
    
    def __init__(self, orientation: str = 'vertical', parent=None):
        super().__init__(parent)
        self._orientation = orientation
        self._level_left = 0.0
        self._level_right = 0.0
        self._peak_left = 0.0
        self._peak_right = 0.0
        
        if orientation == 'vertical':
            self.setFixedWidth(20)
            self.setMinimumHeight(150)
        else:
            self.setFixedHeight(20)
            self.setMinimumWidth(150)
            
        self.setObjectName('levelMeter')
        self.setStyleSheet("""
            QFrame#levelMeter {
                background: #0f0f0f;
                border: 1px solid #2a2a2a;
                border-radius: 2px;
            }
        """)
        
    def set_level(self, left: float, right: float = None):
        """Установить уровень (0.0 - 1.0)."""
        self._level_left = min(1.0, max(0.0, left))
        self._level_right = min(1.0, max(0.0, right)) if right is not None else left
        
        # Обновление пиков
        if self._level_left > self._peak_left:
            self._peak_left = self._level_left
        if self._level_right > self._peak_right:
            self._peak_right = self._level_right
            
        self.update()
        
    def reset_peaks(self):
        """Сбросить пики."""
        self._peak_left = 0.0
        self._peak_right = 0.0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        if self._orientation == 'vertical':
            self._draw_vertical(painter, w, h)
        else:
            self._draw_horizontal(painter, w, h)
            
    def _draw_vertical(self, painter, w, h):
        # Левый канал
        left_h = int(self._level_left * h)
        right_h = int(self._level_right * h)
        
        # Градиент для уровня
        gradient = QLinearGradient(0, h, 0, 0)
        gradient.setColorAt(0, QColor('#00ff88'))
        gradient.setColorAt(0.6, QColor('#ffeb3b'))
        gradient.setColorAt(0.85, QColor('#ff5252'))
        
        # Левый канал
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(1, h - left_h, w // 2 - 1, left_h)
        
        # Правый канал
        painter.drawRect(w // 2, h - right_h, w // 2 - 1, right_h)
        
        # Пики
        painter.setPen(QPen(QColor('#ffffff'), 2))
        if self._peak_left > 0:
            y = h - int(self._peak_left * h)
            painter.drawLine(0, y, w // 2 - 1, y)
        if self._peak_right > 0:
            y = h - int(self._peak_right * h)
            painter.drawLine(w // 2, y, w - 1, y)
            
    def _draw_horizontal(self, painter, w, h):
        left_w = int(self._level_left * w)
        right_w = int(self._level_right * w)
        
        gradient = QLinearGradient(0, 0, w, 0)
        gradient.setColorAt(0, QColor('#00ff88'))
        gradient.setColorAt(0.6, QColor('#ffeb3b'))
        gradient.setColorAt(0.85, QColor('#ff5252'))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, left_w, h // 2)
        painter.drawRect(0, h // 2, right_w, h // 2)


class TimeDisplay(QFrame):
    """Отображение времени в стиле FL Studio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0.0
        self._duration = 0.0
        
        self.setStyleSheet("""
            QFrame {
                background: #0f0f0f;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 12px;
            }
        """)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(8)
        
        # Текущее время
        self._current_label = QLabel("0:00.000")
        self._current_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 18px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
        """)
        lay.addWidget(self._current_label)
        
        # Разделитель
        sep = QLabel("/")
        sep.setStyleSheet("color: #606060; font-size: 14px;")
        lay.addWidget(sep)
        
        # Общая длительность
        self._duration_label = QLabel("0:00.000")
        self._duration_label.setStyleSheet("""
            QLabel {
                color: #909090;
                font-size: 16px;
                font-family: 'Consolas', monospace;
            }
        """)
        lay.addWidget(self._duration_label)
        
    def set_time(self, current_ms: int, duration_ms: int):
        """Установить текущее время и длительность."""
        self._current = current_ms / 1000.0
        self._duration = duration_ms / 1000.0
        
        self._current_label.setText(self._format_time(current_ms))
        self._duration_label.setText(self._format_time(duration_ms))
        
    def _format_time(self, ms: int) -> str:
        """Форматировать время в M:SS.mmm."""
        seconds = ms / 1000.0
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:06.3f}"


class SeekSlider(QSlider):
    """Слайдер поиска в стиле FL Studio."""
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 1000)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #0f0f0f;
                height: 8px;
                border-radius: 4px;
                border: 1px solid #2a2a2a;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00cc6a);
                width: 16px;
                height: 20px;
                margin: -7px 0;
                border-radius: 4px;
                border: 2px solid #004422;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #44ffaa, stop:1 #00ff88);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00cc6a);
                border-radius: 4px;
            }
        """)


class TransportPanel(QFrame):
    """
    Транспортная панель в стиле FL Studio.
    - Кнопки управления (Play, Pause, Stop, Record)
    - Слайдер поиска
    - Отображение времени
    - Визуализатор уровня
    - A/B сравнение
    """
    
    play_toggled = pyqtSignal(bool)
    stop_requested = pyqtSignal()
    seek_requested = pyqtSignal(float)  # позиция в секундах
    ab_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transportPanel')
        self._player = None
        self._current_file = ''
        self._ab_original = ''
        self._ab_processed = ''
        self._is_b = False
        self._available = False
        
        self._setup_ui()
        self._setup_player()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)
        
        # Заголовок
        header = QLabel("🎹 TRANSPORT")
        header.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                background: #1a1a1a;
                border-radius: 4px;
            }
        """)
        lay.addWidget(header)
        
        # Верхняя строка: кнопки транспорта
        transport_row = QHBoxLayout()
        transport_row.setSpacing(8)
        
        # Кнопка Play/Pause
        self.btn_play = TransportButton("▶", "Воспроизведение (Пробел)")
        self.btn_play.clicked.connect(self._toggle_play)
        transport_row.addWidget(self.btn_play)
        
        # Кнопка Stop
        self.btn_stop = TransportButton("⏹", "Стоп")
        self.btn_stop.clicked.connect(self._stop)
        transport_row.addWidget(self.btn_stop)
        
        # Кнопка Record (для превью)
        self.btn_preview = TransportButton("🎤", "Предпросмотр эффектов")
        self.btn_preview.clicked.connect(self._preview)
        transport_row.addWidget(self.btn_preview)
        
        transport_row.addStretch()
        
        # A/B переключатель
        self.btn_ab = QPushButton("A")
        self.btn_ab.setFixedSize(44, 44)
        self.btn_ab.setCheckable(True)
        self.btn_ab.setObjectName('transportBtn')
        self.btn_ab.setToolTip("A/B сравнение: Оригинальный / Обработанный")
        self.btn_ab.setStyleSheet("""
            QPushButton#transportBtn {
                background: #1a1a1a;
                border: 2px solid #3a3a3a;
                border-radius: 22px;
                color: #909090;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#transportBtn:checked {
                background: #00ff88;
                border-color: #00ff88;
                color: #0f0f0f;
            }
            QPushButton#transportBtn:hover:!checked {
                border-color: #00ff88;
                color: #00ff88;
            }
        """)
        self.btn_ab.toggled.connect(self._on_ab_toggled)
        self.btn_ab.setEnabled(False)
        transport_row.addWidget(self.btn_ab)
        
        # Визуализатор уровня
        self.level_meter = LevelMeter('vertical')
        transport_row.addWidget(self.level_meter)
        
        lay.addLayout(transport_row)
        
        # Слайдер поиска
        self.seek_slider = SeekSlider()
        self.seek_slider.sliderMoved.connect(self._on_seek)
        lay.addWidget(self.seek_slider)
        
        # Отображение времени
        self.time_display = TimeDisplay()
        lay.addWidget(self.time_display)
        
        # Инфо о файле
        self.file_info = QLabel("Нет файла")
        self.file_info.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 11px;
                padding: 4px;
            }
        """)
        lay.addWidget(self.file_info)
        
    def _setup_player(self):
        """Инициализация медиаплеера."""
        try:
            self._player = QMediaPlayer()
            self._available = True
            
            self._player.positionChanged.connect(self._on_position)
            self._player.durationChanged.connect(self._on_duration)
            self._player.stateChanged.connect(self._on_state_changed)
            
            # Timer для обновления визуализатора
            self._meter_timer = QTimer(self)
            self._meter_timer.setInterval(50)
            self._meter_timer.timeout.connect(self._update_meter)
            
        except ImportError:
            self._available = False
            self.file_info.setText("QMediaPlayer недоступен")
            
    def load_file(self, file_path: str):
        """Загрузить файл для воспроизведения."""
        if not self._available or not file_path or not os.path.isfile(file_path):
            return
            
        self._current_file = file_path
        self._ab_original = file_path
        self._is_b = False
        self.btn_ab.setChecked(False)
        
        media = QMediaContent(QUrl.fromLocalFile(file_path))
        self._player.setMedia(media)
        
        # Извлечение названия файла
        file_name = os.path.basename(file_path)
        self.file_info.setText(f"🎵 {file_name}")
        
        # Сброс UI
        self.seek_slider.setValue(0)
        self.time_display.set_time(0, 0)
        self.btn_play.setText("▶")
        
    def set_processed_file(self, file_path: str):
        """Установить обработанный файл для A/B сравнения."""
        if not file_path or not os.path.isfile(file_path):
            self.btn_ab.setEnabled(False)
            return

        self._ab_processed = file_path
        self.btn_ab.setEnabled(True)

    def set_playhead(self, position_sec: float):
        """Установить позицию playhead."""
        if self._player and self._player.duration() > 0:
            position_ms = int(position_sec * 1000)
            self._player.setPosition(position_ms)
        
    def _toggle_play(self):
        """Переключить воспроизведение."""
        if not self._player:
            return
            
        from PyQt5.QtMultimedia import QMediaPlayer
        
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.pause()
            self.btn_play.setText("▶")
            self._meter_timer.stop()
        else:
            self._player.play()
            self.btn_play.setText("⏸")
            self._meter_timer.start()
            
        self.play_toggled.emit(self._player.state() == QMediaPlayer.PlayingState)
        
    def _stop(self):
        """Остановить воспроизведение."""
        if self._player:
            self._player.stop()
            self.btn_play.setText("▶")
            self._meter_timer.stop()
            self.seek_slider.setValue(0)
            self.stop_requested.emit()
            
    def _preview(self):
        """Предпросмотр эффектов (заглушка)."""
        # В будущем здесь будет предпросмотр с эффектами
        pass
        
    def _on_ab_toggled(self, checked: bool):
        """Переключение A/B."""
        self._is_b = checked
        
        if self._is_b and self._ab_processed:
            path = self._ab_processed
            self.btn_ab.setText("B")
        else:
            path = self._ab_original
            self.btn_ab.setText("A")
            
        # Сохранение позиции и состояния
        was_playing = False
        pos = 0
        from PyQt5.QtMultimedia import QMediaPlayer
        if self._player.state() == QMediaPlayer.PlayingState:
            was_playing = True
            pos = self._player.position()
            
        # Переключение файла
        media = QMediaContent(QUrl.fromLocalFile(path))
        self._player.setMedia(media)
        
        if was_playing:
            self._player.play()
            self._player.setPosition(pos)
            
        self.ab_toggled.emit(self._is_b)
        
    def _on_seek(self, position: int):
        """Перемещение по треку."""
        if self._player and self._player.duration() > 0:
            seek_ms = int(position / 1000 * self._player.duration())
            self._player.setPosition(seek_ms)
            self.seek_requested.emit(seek_ms / 1000.0)
            
    def _on_position(self, position_ms: int):
        """Обновление позиции воспроизведения."""
        duration_ms = self._player.duration() if self._player else 0
        self.time_display.set_time(position_ms, duration_ms)
        
        if duration_ms > 0:
            self.seek_slider.setValue(int(position_ms / duration_ms * 1000))
            
    def _on_duration(self, duration_ms: int):
        """Установка длительности."""
        current_ms = self._player.position() if self._player else 0
        self.time_display.set_time(current_ms, duration_ms)
        
    def _on_state_changed(self, state):
        """Изменение состояния плеера."""
        from PyQt5.QtMultimedia import QMediaPlayer
        if state != QMediaPlayer.PlayingState:
            self.btn_play.setText("▶")
            self._meter_timer.stop()
            self.level_meter.set_level(0, 0)
            
    def _update_meter(self):
        """Обновление визуализатора уровня."""
        if not self._player:
            return
            
        # Симуляция уровня (в будущем - реальные данные)
        from PyQt5.QtMultimedia import QMediaPlayer
        if self._player.state() == QMediaPlayer.PlayingState:
            # Симуляция на основе позиции
            import random
            level = 0.3 + random.random() * 0.5
            self.level_meter.set_level(level, level)
        else:
            self.level_meter.set_level(0, 0)
