"""Главное окно VK Track Modifier — современный интерфейс."""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QSplitter, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

from ..config import Config
from ..constants import APP_NAME, APP_VERSION
from .fl_styles import STYLESHEET
from .waveform_widget import WaveformWidget
from .effects_panel import EffectsPanel
from .files_panel import FilesPanel
from .structure_panel import StructurePanelWidget
from .transport_widget import TransportWidget
from .metadata_widget import MetadataWidget
from ..core.track_info import TrackInfo
from ..core.worker import ProcessingPool

logger = logging.getLogger('vk_modifier.ui.main_window')


class MainWindow(QMainWindow):
    """Современное главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.tracks = []
        self.current_index = -1
        self.pool = ProcessingPool(max_workers=self.config.get('max_workers', 2))
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 700)
        
        # Центральное окно
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Верхняя панель (Transport)
        self.transport = TransportWidget()
        self.transport.setMaximumHeight(160)
        main_layout.addWidget(self.transport)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        
        # Левая панель (Файлы + Эффекты)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.files_panel = FilesPanel()
        self.files_panel.file_selected.connect(self._on_file_selected)
        self.files_panel.btn_add.clicked.connect(self._add_files)
        self.files_panel.btn_remove.clicked.connect(self._remove_selected)
        left_layout.addWidget(self.files_panel, 1)
        
        self.effects_panel = EffectsPanel()
        self.effects_panel.settings_changed.connect(self._on_settings_changed)
        left_layout.addWidget(self.effects_panel)
        
        splitter.addWidget(left_widget)
        
        # Центральная панель (Waveform + Structure)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)
        
        self.waveform = WaveformWidget()
        self.waveform.position_changed.connect(self.transport.set_position)
        self.waveform.marker_changed.connect(self._on_marker_changed)
        center_layout.addWidget(self.waveform, 2)
        
        self.structure_panel = StructurePanelWidget()
        self.structure_panel.settings_changed.connect(self._on_structure_changed)
        center_layout.addWidget(self.structure_panel, 1)
        
        splitter.addWidget(center_widget)
        
        # Правая панель (Metadata + Export + Start)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        self.metadata_widget = MetadataWidget()
        right_layout.addWidget(self.metadata_widget, 2)
        
        # Кнопка запуска
        self.btn_start = QPushButton("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setObjectName('successBtn')
        self.btn_start.setMinimumHeight(60)
        self.btn_start.clicked.connect(self._start_processing)
        right_layout.addWidget(self.btn_start)
        
        splitter.addWidget(right_widget)
        
        # Пропорции
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter, 1)
        
        # Статус бар
        self._setup_status_bar()
        
        # Применяем стили
        self.setStyleSheet(STYLESHEET)
        
    def _setup_status_bar(self):
        """Настройка статус бара."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_files = QLabel("0 файлов")
        self.status_version = QLabel(f"v{APP_VERSION}")
        
        self.status_bar.addWidget(self.status_files)
        self.status_bar.addPermanentWidget(self.status_version)
        
    def _connect_signals(self):
        """Подключение сигналов."""
        self.pool.file_step.connect(self._on_file_step)
        self.pool.file_complete.connect(self._on_file_complete)
        self.pool.all_complete.connect(self._on_all_complete)
        
    def _add_files(self):
        """Добавить файлы."""
        last_dir = self.config.get('last_input_dir', '')
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите MP3 файлы", last_dir, "MP3 (*.mp3)"
        )
        if files:
            self.config.set('last_input_dir', os.path.dirname(files[0]))
            self.files_panel.add_files(files)
            self._load_files_metadata(files)
            
    def _load_files_metadata(self, paths):
        """Загрузить метаданные файлов."""
        for path in paths:
            track = TrackInfo(path)
            track.compute_hash()
            track.load_metadata()
            self.tracks.append(track)
            
        if len(self.tracks) == 1:
            self._load_track(0)
            
    def _on_file_selected(self, index):
        """Выбран файл в списке."""
        if 0 <= index < len(self.tracks):
            self._load_track(index)
            
    def _load_track(self, index):
        """Загрузить трек."""
        track = self.tracks[index]
        if track:
            self.current_index = index
            self.waveform.load_audio(track.file_path)
            self.structure_panel.set_duration(track.duration_sec)
            self.transport.load_file(track.file_path)
            self.metadata_widget.load_track(track)
            
    def _on_marker_changed(self, marker_type, value):
        """Изменён маркер."""
        self.structure_panel.set_marker(marker_type, value)
        
    def _on_settings_changed(self):
        """Изменены настройки эффектов."""
        pass
        
    def _on_structure_changed(self):
        """Изменена структура."""
        settings = self.structure_panel.get_settings()
        self.waveform.set_markers(
            settings['trim_start'],
            settings['cut_start'],
            settings['cut_end'],
        )
        
    def _remove_selected(self):
        """Удалить выбранный файл."""
        self.files_panel.remove_selected()
        
    def _start_processing(self):
        """Запуск обработки."""
        if not self.tracks:
            QMessageBox.warning(self, "Внимание", "Добавьте файлы для обработки")
            return
            
        settings = self.effects_panel.get_settings()
        settings.update(self.structure_panel.get_settings())
        settings.update(self.metadata_widget.get_settings())
        
        self.btn_start.setEnabled(False)
        self.btn_start.setText("⏳ ОБРАБОТКА...")
        
        logger.info(f"Запуск обработки: {len(self.tracks)} файлов")
        
    def _on_file_step(self, index, total):
        """Шаг обработки."""
        pass
        
    def _on_file_complete(self, index, success):
        """Файл обработан."""
        pass
        
    def _on_all_complete(self, results):
        """Обработка завершена."""
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
