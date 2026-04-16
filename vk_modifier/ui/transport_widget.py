"""Транспортная панель управления воспроизведением."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QSlider,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class TransportWidget(QFrame):
    """Панель управления воспроизведением."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName('headerFrame')
        
        self._player = None
        self._available = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        header = QLabel("🎹 TRANSPORT")
        header.setObjectName('headerLabel')
        layout.addWidget(header)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setObjectName('transportBtn')
        self.btn_play.setFixedSize(50, 50)
        self.btn_play.clicked.connect(self._toggle_play)
        btn_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setObjectName('transportBtn')
        self.btn_stop.setFixedSize(50, 50)
        self.btn_stop.clicked.connect(self._stop)
        btn_layout.addWidget(self.btn_stop)
        
        btn_layout.addStretch()
        
        # Слайдер позиции
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1a1a2e;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #00adb5, stop:1 #e94560);
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00adb5, stop:1 #e94560);
                border-radius: 4px;
            }
        """)
        self.seek_slider.sliderMoved.connect(self._seek)
        btn_layout.addWidget(self.seek_slider, 1)
        
        btn_layout.addStretch()
        
        # Время
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("""
            color: #00ff88;
            font-size: 16px;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            padding: 8px 15px;
            background: #1a1a2e;
            border-radius: 6px;
        """)
        btn_layout.addWidget(self.time_label)
        
        layout.addLayout(btn_layout)
        
        # Инфо о файле
        self.file_info = QLabel("Нет файла")
        self.file_info.setStyleSheet("color: #606060; font-size: 11px;")
        layout.addWidget(self.file_info)
        
        # Инициализация плеера
        self._init_player()
        
    def _init_player(self):
        """Инициализация медиаплеера."""
        try:
            self._player = QMediaPlayer()
            self._available = True
            
            self._player.positionChanged.connect(self._on_position)
            self._player.durationChanged.connect(self._on_duration)
            
        except ImportError:
            self._available = False
            self.file_info.setText("QMediaPlayer недоступен")
            
    def load_file(self, file_path):
        """Загрузить файл."""
        if not self._available or not file_path or not os.path.isfile(file_path):
            return
            
        media = QMediaContent(QUrl.fromLocalFile(file_path))
        self._player.setMedia(media)
        
        file_name = os.path.basename(file_path)
        self.file_info.setText(f"🎵 {file_name}")
        
        self.seek_slider.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        
    def _toggle_play(self):
        """Переключить воспроизведение."""
        if not self._player:
            return
            
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.pause()
            self.btn_play.setText("▶")
        else:
            self._player.play()
            self.btn_play.setText("⏸")
            
    def _stop(self):
        """Остановить."""
        if self._player:
            self._player.stop()
            self.btn_play.setText("▶")
            self.seek_slider.setValue(0)
            
    def _seek(self, position):
        """Перемотка."""
        if self._player and self._player.duration() > 0:
            seek_ms = int(position / 1000 * self._player.duration())
            self._player.setPosition(seek_ms)
            
    def set_position(self, position_sec):
        """Установить позицию."""
        if self._player and self._player.duration() > 0:
            position_ms = int(position_sec * 1000)
            self._player.setPosition(position_ms)
            
    def _on_position(self, position_ms):
        """Обновление позиции."""
        duration_ms = self._player.duration() if self._player else 0
        
        if duration_ms > 0:
            self.seek_slider.setValue(int(position_ms / duration_ms * 1000))
            
        self.time_label.setText(f"{self._fmt(position_ms)} / {self._fmt(duration_ms)}")
        
    def _on_duration(self, duration_ms):
        """Установка длительности."""
        position_ms = self._player.position() if self._player else 0
        self.time_label.setText(f"{self._fmt(position_ms)} / {self._fmt(duration_ms)}")
        
    def _fmt(self, ms):
        """Форматирование времени."""
        seconds = ms // 1000
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"
