"""Главное окно в стиле FL Studio."""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QSplitter, QToolBar,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QKeySequence, QFont, QDesktopServices

from ..config import Config
from ..constants import APP_NAME, APP_VERSION
from .fl_styles import FL_STYLESHEET
from .waveform_editor import WaveformEditor
from .channel_rack import ChannelRack
from .structure_panel import StructurePanel
from .transport_panel import TransportPanel
from .tabs.metadata_tab import MetadataTab
from .tabs.export_tab import ExportTab
from ..core.track_info import TrackInfo
from ..core.worker import ProcessingPool
from ..core.presets import BUILTIN_PRESETS, get_preset_settings

logger = logging.getLogger('vk_modifier.ui.fl_main_window')


class FileListFrame(QFrame):
    """Список файлов в стиле FL Studio Browser."""
    
    file_selected = pyqtSignal(int)
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('fileBrowser')
        self.setStyleSheet("""
            QFrame#fileBrowser {
                background: #1e1e1e;
                border: 1px solid #3a3a3a;
            }
        """)
        
        self._files = []
        self._selected_index = -1
        
        self._setup_ui()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        
        # Заголовок
        header = QLabel("📁 BROWSER")
        header.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
                background: #1a1a1a;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        lay.addWidget(header)
        
        # Кнопки управления
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background: #242424; border-bottom: 1px solid #3a3a3a;")
        btn_lay = QHBoxLayout(btn_frame)
        btn_lay.setContentsMargins(8, 8, 8, 8)
        btn_lay.setSpacing(6)
        
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background: #00ff88;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #0f0f0f;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #44ffaa;
            }
        """)
        btn_lay.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton("🗑️ Удалить")
        self.btn_remove.setStyleSheet("""
            QPushButton {
                background: #ff5252;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff7777;
            }
            QPushButton:disabled {
                background: #3a3a3a;
                color: #606060;
            }
        """)
        self.btn_remove.setEnabled(False)
        btn_lay.addWidget(self.btn_remove)
        
        lay.addWidget(btn_frame)
        
        # Список файлов
        self.file_list = QFrame()
        self.file_list.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
            }
        """)
        self.file_list_layout = QVBoxLayout(self.file_list)
        self.file_list_layout.setContentsMargins(4, 4, 4, 4)
        self.file_list_layout.setSpacing(2)
        lay.addWidget(self.file_list, 1)
        
        # Инфо
        self.info_label = QLabel("Файлов: 0")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 10px;
                padding: 6px 12px;
                background: #1a1a1a;
                border-top: 1px solid #3a3a3a;
            }
        """)
        lay.addWidget(self.info_label)
        
    def add_files(self, paths: list):
        """Добавить файлы в список."""
        for path in paths:
            if path not in self._files:
                self._files.append(path)
                self._create_file_item(len(self._files) - 1, path)
        self._update_info()
        
    def _create_file_item(self, index: int, path: str):
        """Создать элемент файла."""
        item = QFrame()
        item.setObjectName(f'fileItem{index}')
        item.setStyleSheet("""
            QFrame {
                background: #242424;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 8px;
            }
            QFrame:hover {
                background: #2d2d2d;
                border-color: #3a3a3a;
            }
            QFrame:selected {
                background: #2d2d2d;
                border-color: #00ff88;
            }
        """)
        item.mousePressEvent = lambda e, idx=index: self._on_item_click(idx)
        
        lay = QHBoxLayout(item)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)
        
        # Иконка
        icon = QLabel("🎵")
        icon.setStyleSheet("font-size: 16px;")
        lay.addWidget(icon)
        
        # Информация
        info_lay = QVBoxLayout()
        name = os.path.basename(path)
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        info_lay.addWidget(name_label)
        
        path_label = QLabel(path[:50] + "..." if len(path) > 50 else path)
        path_label.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 9px;
            }
        """)
        info_lay.addWidget(path_label)
        
        lay.addLayout(info_lay)
        
        self.file_list_layout.addWidget(item)
        
    def _on_item_click(self, index: int):
        """Клик по элементу файла."""
        self._selected_index = index
        self._update_selection()
        self.file_selected.emit(index)
        
    def _update_selection(self):
        """Обновить выделение."""
        for i in range(self.file_list_layout.count()):
            item = self.file_list_layout.itemAt(i).widget()
            if item:
                if i == self._selected_index:
                    item.setStyleSheet("""
                        QFrame {
                            background: #2d2d2d;
                            border: 1px solid #00ff88;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
                else:
                    item.setStyleSheet("""
                        QFrame {
                            background: #242424;
                            border: 1px solid transparent;
                            border-radius: 4px;
                            padding: 8px;
                        }
                        QFrame:hover {
                            background: #2d2d2d;
                            border-color: #3a3a3a;
                        }
                    """)
                    
    def _update_info(self):
        """Обновить информацию."""
        total_size = sum(
            os.path.getsize(f) for f in self._files if os.path.exists(f)
        ) / (1024 * 1024)
        self.info_label.setText(f"Файлов: {len(self._files)} · {total_size:.1f} MB")
        self.btn_remove.setEnabled(len(self._files) > 0)
        
    def get_selected_index(self) -> int:
        return self._selected_index
        
    def get_file_path(self, index: int) -> str:
        return self._files[index] if 0 <= index < len(self._files) else ''
        
    def remove_selected(self):
        """Удалить выбранный файл."""
        if self._selected_index < 0:
            return
        self._files.pop(self._selected_index)
        
        # Пересоздать список
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0).widget()
            if item:
                item.deleteLater()
                
        for i, path in enumerate(self._files):
            self._create_file_item(i, path)
            
        self._selected_index = -1
        self._update_info()
        
    def clear(self):
        """Очистить список."""
        self._files.clear()
        self._selected_index = -1
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0).widget()
            if item:
                item.deleteLater()
        self._update_info()


class FLMainWindow(QMainWindow):
    """Главное окно в стиле FL Studio."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.tracks_info = []
        self.output_dir = self.config.get('output_dir', '')
        self.pool = ProcessingPool(max_workers=self.config.get('max_workers', 2))
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - FL Studio Edition")
        self.setGeometry(80, 80, 1600, 1000)
        self.setMinimumSize(1200, 700)
        
        # Центральное окно
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # Верхняя панель (Transport)
        self.transport = TransportPanel()
        self.transport.setMaximumHeight(180)
        main_lay.addWidget(self.transport)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #3a3a3a;
            }
            QSplitter::handle:hover {
                background: #00ff88;
            }
        """)
        
        # Левая панель (Browser + Channel Rack)
        left_panel = QWidget()
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)
        
        # Browser
        self.file_browser = FileListFrame()
        self.file_browser.btn_add.clicked.connect(self._add_files)
        self.file_browser.btn_remove.clicked.connect(self._remove_selected)
        left_lay.addWidget(self.file_browser, 1)
        
        # Channel Rack
        self.channel_rack = ChannelRack()
        self.channel_rack.setMaximumHeight(400)
        left_lay.addWidget(self.channel_rack)
        
        splitter.addWidget(left_panel)
        
        # Центральная панель (Waveform + Playlist)
        center_panel = QWidget()
        center_lay = QVBoxLayout(center_panel)
        center_lay.setContentsMargins(8, 8, 8, 8)
        center_lay.setSpacing(8)
        
        # Waveform Editor
        self.waveform = WaveformEditor()
        self.waveform.position_changed.connect(self.transport.set_playhead)
        self.waveform.marker_moved.connect(self._on_marker_moved)
        center_lay.addWidget(self.waveform, 2)
        
        # Structure Panel (Playlist)
        self.structure = StructurePanel()
        self.structure.settings_changed.connect(self._on_structure_changed)
        center_lay.addWidget(self.structure, 1)
        
        splitter.addWidget(center_panel)
        
        # Правая панель (Metadata + Export)
        right_panel = QWidget()
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)
        
        # Metadata Tab
        self.metadata_tab = MetadataTab()
        right_lay.addWidget(self.metadata_tab, 1)
        
        # Export Tab
        self.export_tab = ExportTab()
        right_lay.addWidget(self.export_tab)
        
        # Кнопка запуска
        self.btn_start = QPushButton("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setObjectName('accentBtn')
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setStyleSheet("""
            QPushButton#accentBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00cc6a);
                border: 2px solid #004422;
                border-radius: 8px;
                padding: 16px;
                color: #0f0f0f;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#accentBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #44ffaa, stop:1 #00ff88);
            }
            QPushButton#accentBtn:pressed {
                background: #00cc6a;
            }
        """)
        self.btn_start.clicked.connect(self._start_processing)
        right_lay.addWidget(self.btn_start)
        
        splitter.addWidget(right_panel)
        
        # Пропорции splitter
        splitter.setStretchFactor(0, 1)  # Left
        splitter.setStretchFactor(1, 2)  # Center
        splitter.setStretchFactor(2, 1)  # Right
        
        main_lay.addWidget(splitter, 1)
        
        # Status bar
        self._setup_status_bar()
        
        # Применяем стили
        self.setStyleSheet(FL_STYLESHEET)
        
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
        # Выбор файла
        self.file_browser.file_selected.connect(self._on_file_selected)
        
        # Транспорт
        self.transport.play_toggled.connect(self._on_play_toggled)
        
        # Обработка
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
            self.file_browser.add_files(files)
            self._load_files_metadata(files)
            
    def _load_files_metadata(self, paths: list):
        """Загрузить метаданные файлов."""
        for path in paths:
            track = TrackInfo(path)
            track.compute_hash()
            track.load_metadata()
            self.tracks_info.append(track)
            
        # Загрузить первый файл в waveform
        if len(self.tracks_info) == 1:
            self._load_track_to_waveform(0)
            
    def _on_file_selected(self, index: int):
        """Выбран файл в списке."""
        if 0 <= index < len(self.tracks_info):
            self._load_track_to_waveform(index)
            
    def _load_track_to_waveform(self, index: int):
        """Загрузить трек в waveform редактор."""
        track = self.tracks_info[index]
        if track:
            self.waveform.load_audio(track.file_path)
            self.structure.set_track_duration(track.duration_sec)
            self.transport.load_file(track.file_path)
            
    def _on_marker_moved(self, marker_type: str, value: float):
        """Перемещён маркер."""
        # Обновить структуру
        pass
        
    def _on_structure_changed(self):
        """Изменена структура."""
        settings = self.structure.get_settings()
        self.waveform.set_markers(
            settings['trim_start_sec'],
            settings['cut_start_sec'],
            settings['cut_end_sec'],
        )
        
    def _on_play_toggled(self, playing: bool):
        """Переключено воспроизведение."""
        pass
        
    def _remove_selected(self):
        """Удалить выбранный файл."""
        self.file_browser.remove_selected()
        
    def _start_processing(self):
        """Запуск обработки."""
        if not self.file_browser._files:
            QMessageBox.warning(self, "Внимание", "Добавьте файлы для обработки")
            return
            
        settings = self.channel_rack.get_settings()
        settings.update(self.structure.get_settings())
        settings.update(self.export_tab.get_settings())
        
        # Запуск обработки
        self.btn_start.setEnabled(False)
        self.btn_start.setText("⏳ ОБРАБОТКА...")
        
        # Здесь будет запуск worker
        logger.info(f"Запуск обработки с настройками: {settings}")
        
    def _on_file_step(self, index: int, total: int):
        """Шаг обработки файла."""
        pass
        
    def _on_file_complete(self, index: int, success: bool):
        """Файл обработан."""
        pass
        
    def _on_all_complete(self, results: list):
        """Обработка завершена."""
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        
    def _apply_preset(self, preset_name: str):
        """Применить пресет."""
        if preset_name in BUILTIN_PRESETS:
            settings = get_preset_settings(preset_name)
            self.channel_rack.apply_settings(settings)
