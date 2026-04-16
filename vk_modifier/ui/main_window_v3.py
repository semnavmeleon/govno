"""Главное окно — верхние вкладки, центр waveform, справа экспорт."""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QFileDialog, QMessageBox,
    QStatusBar, QSplitter, QTabWidget, QScrollArea,
    QGridLayout, QSpinBox, QComboBox, QCheckBox, QLineEdit,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

from ..config import Config
from ..constants import APP_NAME, APP_VERSION
from .fl_styles import STYLESHEET
from .waveform_widget import WaveformWidget
from ..core.track_info import TrackInfo
from ..core.worker import ProcessingPool

logger = logging.getLogger('vk_modifier.ui.main_window')


class EffectsTab(QWidget):
    """Вкладка эффектов."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("🎛️ ЭФФЕКТЫ")
        title.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold;")
        layout.addWidget(title, 0, 0, 1, 2)
        
        # Pitch
        layout.addWidget(self._label("Тональность:"), 1, 0)
        self.pitch_spin = QSpinBox()
        self.pitch_spin.setRange(-24, 24)
        self.pitch_spin.setValue(0)
        self.pitch_spin.setSuffix(" пт")
        self.pitch_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.pitch_spin, 1, 1)
        
        # Speed
        layout.addWidget(self._label("Скорость:"), 2, 0)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(95, 105)
        self.speed_spin.setValue(100)
        self.speed_spin.setSuffix("%")
        self.speed_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.speed_spin, 2, 1)
        
        # Phase
        layout.addWidget(self._label("Фазовый сдвиг:"), 3, 0)
        self.phase_spin = QSpinBox()
        self.phase_spin.setRange(0, 10)
        self.phase_spin.setValue(0)
        self.phase_spin.setSuffix(" мс")
        self.phase_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.phase_spin, 3, 1)
        
        # Noise
        layout.addWidget(self._label("Розовый шум:"), 4, 0)
        self.noise_spin = QSpinBox()
        self.noise_spin.setRange(0, 100)
        self.noise_spin.setValue(0)
        self.noise_spin.setSuffix("%")
        self.noise_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.noise_spin, 4, 1)
        
        # Fade In
        layout.addWidget(self._label("Fade In:"), 5, 0)
        self.fade_in_spin = QSpinBox()
        self.fade_in_spin.setRange(0, 30)
        self.fade_in_spin.setValue(0)
        self.fade_in_spin.setSuffix(" сек")
        self.fade_in_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.fade_in_spin, 5, 1)
        
        # Fade Out
        layout.addWidget(self._label("Fade Out:"), 6, 0)
        self.fade_out_spin = QSpinBox()
        self.fade_out_spin.setRange(0, 30)
        self.fade_out_spin.setValue(0)
        self.fade_out_spin.setSuffix(" сек")
        self.fade_out_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.fade_out_spin, 6, 1)
        
        # Чекбоксы
        self.chk_eq = QCheckBox("Эквализация")
        self.chk_eq.setStyleSheet("color: #ffffff; font-size: 13px;")
        self.chk_eq.toggled.connect(self.settings_changed)
        layout.addWidget(self.chk_eq, 7, 0, 1, 2)
        
        self.eq_combo = QComboBox()
        self.eq_combo.addItems(["Лёгкая", "Средняя", "Сильная", "Boost середины", "Boost верхов"])
        self.eq_combo.setEnabled(False)
        self.eq_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addWidget(self.eq_combo, 8, 0, 1, 2)
        
        self.chk_compression = QCheckBox("Компрессия")
        self.chk_compression.setStyleSheet("color: #ffffff; font-size: 13px;")
        self.chk_compression.toggled.connect(self.settings_changed)
        layout.addWidget(self.chk_compression, 9, 0, 1, 2)
        
        self.chk_ultrasound = QCheckBox("Ультразвук (19-22kHz)")
        self.chk_ultrasound.setStyleSheet("color: #ffffff; font-size: 13px;")
        self.chk_ultrasound.toggled.connect(self.settings_changed)
        layout.addWidget(self.chk_ultrasound, 10, 0, 1, 2)
        
        self.chk_dc_shift = QCheckBox("DC сдвиг")
        self.chk_dc_shift.setStyleSheet("color: #ffffff; font-size: 13px;")
        self.chk_dc_shift.toggled.connect(self.settings_changed)
        layout.addWidget(self.chk_dc_shift, 11, 0, 1, 2)
        
        layout.setRowStretch(12, 1)
        
    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        return lbl
        
    def get_settings(self):
        return {
            'pitch_semitones': self.pitch_spin.value(),
            'speed_factor': self.speed_spin.value() / 100,
            'eq_preset_index': self.eq_combo.currentIndex() if self.chk_eq.isChecked() else -1,
            'compression_enabled': self.chk_compression.isChecked(),
            'phase_delay_ms': self.phase_spin.value(),
            'noise_amplitude': self.noise_spin.value() / 10000,
            'ultrasound_enabled': self.chk_ultrasound.isChecked(),
            'dc_shift_enabled': self.chk_dc_shift.isChecked(),
            'fade_in_sec': self.fade_in_spin.value(),
            'fade_out_sec': self.fade_out_spin.value(),
        }


class StructureTab(QWidget):
    """Вкладка структуры."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("📋 СТРУКТУРА")
        title.setStyleSheet("color: #00adb5; font-size: 20px; font-weight: bold;")
        layout.addWidget(title, 0, 0, 1, 2)
        
        # Trim
        layout.addWidget(QLabel("✂️ Обрезать начало:"), 1, 0)
        self.trim_spin = QSpinBox()
        self.trim_spin.setRange(0, 9999)
        self.trim_spin.setValue(0)
        self.trim_spin.setSuffix(" сек")
        self.trim_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.trim_spin, 1, 1)
        
        # Cut
        layout.addWidget(QLabel("🔪 Вырезать от:"), 2, 0)
        self.cut_start_spin = QSpinBox()
        self.cut_start_spin.setRange(0, 9999)
        self.cut_start_spin.setValue(0)
        self.cut_start_spin.setSuffix(" сек")
        self.cut_start_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.cut_start_spin, 2, 1)
        
        layout.addWidget(QLabel("🔪 Вырезать до:"), 3, 0)
        self.cut_end_spin = QSpinBox()
        self.cut_end_spin.setRange(0, 9999)
        self.cut_end_spin.setValue(0)
        self.cut_end_spin.setSuffix(" сек")
        self.cut_end_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.cut_end_spin, 3, 1)
        
        # Silence
        layout.addWidget(QLabel("➕ Тишина в конец:"), 4, 0)
        self.silence_spin = QSpinBox()
        self.silence_spin.setRange(0, 999)
        self.silence_spin.setValue(0)
        self.silence_spin.setSuffix(" сек")
        self.silence_spin.valueChanged.connect(self.settings_changed)
        layout.addWidget(self.silence_spin, 4, 1)
        
        layout.setRowStretch(5, 1)
        
    def get_settings(self):
        return {
            'trim_start_sec': self.trim_spin.value(),
            'cut_start_sec': float(self.cut_start_spin.value()),
            'cut_end_sec': float(self.cut_end_spin.value()),
            'silence_end_sec': self.silence_spin.value(),
        }


class MetadataTab(QWidget):
    """Вкладка метаданных."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("🎼 МЕТАДАННЫЕ")
        title.setStyleSheet("color: #ffaa00; font-size: 20px; font-weight: bold;")
        layout.addWidget(title, 0, 0, 1, 2)
        
        # Шаблон
        layout.addWidget(QLabel("Шаблон имени:"), 1, 0)
        self.filename_template = QLineEdit()
        self.filename_template.setText("{prefix}_{counter:03d}_{original_name}")
        self.filename_template.textChanged.connect(self.settings_changed)
        layout.addWidget(self.filename_template, 1, 1)
        
        # Префикс
        layout.addWidget(QLabel("Префикс:"), 2, 0)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("VK")
        self.prefix_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.prefix_edit, 2, 1)
        
        # Тег
        layout.addWidget(QLabel("Тег:"), 3, 0)
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("REUPLOAD")
        self.tag_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.tag_edit, 3, 1)
        
        # Название
        layout.addWidget(QLabel("Название:"), 4, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Оставить оригинал")
        self.title_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.title_edit, 4, 1)
        
        # Исполнитель
        layout.addWidget(QLabel("Исполнитель:"), 5, 0)
        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Оставить оригинал")
        self.artist_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.artist_edit, 5, 1)
        
        # Альбом
        layout.addWidget(QLabel("Альбом:"), 6, 0)
        self.album_edit = QLineEdit()
        self.album_edit.setPlaceholderText("Оставить оригинал")
        self.album_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.album_edit, 6, 1)
        
        # Год
        layout.addWidget(QLabel("Год:"), 7, 0)
        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("2024")
        self.year_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.year_edit, 7, 1)
        
        # Жанр
        layout.addWidget(QLabel("Жанр:"), 8, 0)
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Pop, Rock...")
        self.genre_edit.textChanged.connect(self.settings_changed)
        layout.addWidget(self.genre_edit, 8, 1)
        
        layout.setRowStretch(9, 1)
        
    def get_settings(self):
        return {
            'filename_template': self.filename_template.text(),
            'brand_prefix': self.prefix_edit.text(),
            'brand_tag': self.tag_edit.text(),
            'title': self.title_edit.text(),
            'artist': self.artist_edit.text(),
            'album': self.album_edit.text(),
            'year': self.year_edit.text(),
            'genre': self.genre_edit.text(),
        }


class RightPanel(QScrollArea):
    """Правая панель — импорт, экспорт, информация."""
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Информация о треке
        info_frame = QFrame()
        info_frame.setObjectName('cardFrame')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(10)
        
        info_title = QLabel("🎵 ИНФОРМАЦИЯ")
        info_title.setObjectName('sectionLabel')
        info_layout.addWidget(info_title)
        
        self.track_name = QLabel("Нет трека")
        self.track_name.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background: #1a1a2e;
            border-radius: 8px;
        """)
        self.track_name.setWordWrap(True)
        info_layout.addWidget(self.track_name)
        
        self.track_info = QLabel("")
        self.track_info.setStyleSheet("color: #606060; font-size: 12px;")
        self.track_info.setWordWrap(True)
        info_layout.addWidget(self.track_info)
        
        layout.addWidget(info_frame)
        
        # Импорт/Экспорт
        import_export_frame = QFrame()
        import_export_frame.setObjectName('cardFrame')
        ie_layout = QVBoxLayout(import_export_frame)
        ie_layout.setSpacing(15)
        
        ie_title = QLabel("📤 ИМПОРТ / ЭКСПОРТ")
        ie_title.setObjectName('sectionLabel')
        ie_layout.addWidget(ie_title)
        
        # Кнопка импорта
        self.btn_import = QPushButton("📁 ИМПОРТ ФАЙЛА")
        self.btn_import.setObjectName('primaryBtn')
        self.btn_import.setMinimumHeight(50)
        ie_layout.addWidget(self.btn_import)
        
        # Кнопка экспорта
        self.btn_export = QPushButton("💾 ЭКСПОРТИРОВАТЬ")
        self.btn_export.setObjectName('successBtn')
        self.btn_export.setMinimumHeight(50)
        ie_layout.addWidget(self.btn_export)
        
        # Качество
        ie_layout.addWidget(QLabel("Качество MP3:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["320 kbps", "245 kbps", "175 kbps", "130 kbps"])
        ie_layout.addWidget(self.quality_combo)
        
        # Потоки
        ie_layout.addWidget(QLabel("Потоков обработки:"))
        self.workers_combo = QComboBox()
        self.workers_combo.addItems(["1", "2", "3", "4"])
        self.workers_combo.setCurrentIndex(1)
        ie_layout.addWidget(self.workers_combo)
        
        # Удалить оригиналы
        self.chk_delete = QCheckBox("Удалить оригиналы")
        self.chk_delete.setStyleSheet("color: #ff4757;")
        ie_layout.addWidget(self.chk_delete)
        
        layout.addWidget(import_export_frame)
        
        # Кнопка запуска
        self.btn_start = QPushButton("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setObjectName('successBtn')
        self.btn_start.setMinimumHeight(60)
        self.btn_start.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.btn_start)
        
        layout.addStretch()
        self.setWidget(content)
        
    def set_track_info(self, track):
        """Установить информацию о треке."""
        if track:
            self.track_name.setText(os.path.basename(track.file_path))
            info = []
            if track.duration_sec > 0:
                info.append(f"⏱️ {track.duration_sec:.1f} сек")
            if track.title:
                info.append(f"🎼 {track.title}")
            if track.artist:
                info.append(f"🎤 {track.artist}")
            self.track_info.setText(" · ".join(info) if info else "")


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.tracks = []
        self.current_index = -1
        self.pool = ProcessingPool(max_workers=2)
        
        # Вкладки ещё не созданы
        self._tabs_initialized = False
        self._effects_tab = None
        self._structure_tab = None
        self._metadata_tab = None
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 700)
        
        # Центральное окно
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Левая часть (вкладки + waveform)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Вкладки с настройками (создадим при первом открытии)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background: #16213e;
                border: none;
                border-bottom: 2px solid #2a2a3e;
            }
            QTabBar::tab {
                background: #1a1a2e;
                border: none;
                border-bottom: 3px solid transparent;
                padding: 15px 30px;
                color: #606060;
                font-size: 14px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #16213e;
                color: #ffffff;
                border-bottom-color: #e94560;
            }
            QTabBar::tab:hover:!selected {
                color: #ffffff;
                border-bottom-color: #00adb5;
            }
        """)
        
        # Добавляем пустые виджеты-заглушки
        placeholder1 = QWidget()
        placeholder2 = QWidget()
        placeholder3 = QWidget()
        
        self.tabs.addTab(placeholder1, "🎛️ Эффекты")
        self.tabs.addTab(placeholder2, "📋 Структура")
        self.tabs.addTab(placeholder3, "🎼 Метаданные")
        
        # При переключении вкладки - загружаем контент
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        self.tabs.setMaximumHeight(500)
        left_layout.addWidget(self.tabs)
        
        # Waveform по центру
        self.waveform = WaveformWidget()
        self.waveform.setMinimumHeight(250)
        self.waveform.setStyleSheet("background: #0f0f1a; border: 2px solid #2a2a3e; border-radius: 10px;")
        left_layout.addWidget(self.waveform, 1)
        
        main_layout.addWidget(left_widget, 4)
        
        # Правая панель
        self.right_panel = RightPanel()
        self.right_panel.setMaximumWidth(350)
        self.right_panel.setMinimumWidth(300)
        main_layout.addWidget(self.right_panel, 1)
        
        # Статус бар
        self._setup_status_bar()
        
        # Применяем стили
        self.setStyleSheet(STYLESHEET)
        
    def _on_tab_changed(self, index):
        """Загрузка содержимого вкладки при первом открытии."""
        if not self._tabs_initialized:
            # Создаём вкладки только при первом переключении
            if self._effects_tab is None:
                self._effects_tab = EffectsTab()
                self._effects_tab.settings_changed.connect(self._on_settings_changed)
                self.tabs.widget(0).setLayout(QVBoxLayout())
                self.tabs.widget(0).layout().addWidget(self._effects_tab)
                
            if self._structure_tab is None:
                self._structure_tab = StructureTab()
                self._structure_tab.settings_changed.connect(self._on_settings_changed)
                self.tabs.widget(1).setLayout(QVBoxLayout())
                self.tabs.widget(1).layout().addWidget(self._structure_tab)
                
            if self._metadata_tab is None:
                self._metadata_tab = MetadataTab()
                self._metadata_tab.settings_changed.connect(self._on_settings_changed)
                self.tabs.widget(2).setLayout(QVBoxLayout())
                self.tabs.widget(2).layout().addWidget(self._metadata_tab)
                
            self._tabs_initialized = True
            
    def _on_settings_changed(self):
        """Настройки изменены."""
        pass
        
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
        self.right_panel.btn_import.clicked.connect(self._import_file)
        self.right_panel.btn_export.clicked.connect(self._export_file)
        self.right_panel.btn_start.clicked.connect(self._start_processing)
        
        self.pool.file_step.connect(self._on_file_step)
        self.pool.file_complete.connect(self._on_file_complete)
        self.pool.all_complete.connect(self._on_all_complete)
        
    def _import_file(self):
        """Импорт файла."""
        last_dir = self.config.get('last_input_dir', '')
        file, _ = QFileDialog.getOpenFileName(
            self, "Выберите MP3 файл", last_dir, "MP3 (*.mp3)"
        )
        if file:
            self.config.set('last_input_dir', os.path.dirname(file))
            track = TrackInfo(file)
            track.compute_hash()
            track.load_metadata()
            self.tracks.append(track)
            self.current_index = len(self.tracks) - 1
            self._load_track(track)
            
    def _load_track(self, track):
        """Загрузить трек."""
        self.waveform.load_audio(track.file_path)
        self.right_panel.set_track_info(track)
        self.status_files.setText(f"🎵 {os.path.basename(track.file_path)}")
        
    def _export_file(self):
        """Экспорт файла."""
        QMessageBox.information(self, "Экспорт", "Функция экспорта будет доступна после обработки")
        
    def _start_processing(self):
        """Запуск обработки."""
        if not self.tracks:
            QMessageBox.warning(self, "Внимание", "Импортируйте файл для обработки")
            return
            
        settings = self._effects_tab.get_settings() if self._effects_tab else {}
        settings.update(self._structure_tab.get_settings() if self._structure_tab else {})
        settings.update(self._metadata_tab.get_settings() if self._metadata_tab else {})
        settings['quality'] = str(self.right_panel.quality_combo.currentIndex())
        settings['max_workers'] = int(self.right_panel.workers_combo.currentText())
        settings['delete_originals'] = self.right_panel.chk_delete.isChecked()
        
        self.right_panel.btn_start.setEnabled(False)
        self.right_panel.btn_start.setText("⏳ ОБРАБОТКА...")
        
        logger.info(f"Запуск обработки: {settings}")
        
    def _on_file_step(self, index, total):
        pass
        
    def _on_file_complete(self, index, success):
        pass
        
    def _on_all_complete(self, results):
        self.right_panel.btn_start.setEnabled(True)
        self.right_panel.btn_start.setText("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        QMessageBox.information(self, "Готово", "Обработка завершена успешно!")
