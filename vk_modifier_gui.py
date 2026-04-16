import sys
import os
import random
import subprocess
import json
import tempfile
import hashlib
from datetime import timedelta

import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC, TLEN, TXXX
from mutagen.mp3 import MP3

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QLabel, QPushButton, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QListWidget, QTextEdit,
    QProgressBar, QScrollArea, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QColor, QPalette

CONFIG_FILE = "vk_modifier_config.json"


class TrackInfo:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.duration_sec = 0
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.cover_data = None
        self.cover_mime = "image/jpeg"
        self.bitrate = 0
        self.sample_rate = 0
        self.file_hash = ""


class CoverPreviewLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #777;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #aaa;
                font-size: 11px;
            }
            QLabel:hover {
                border: 1px solid #5a5a5a;
                background-color: #333;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_pixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)
            self.setText("")
        else:
            self.setText("Обложка\nнажмите для\nвыбора")
            super().setPixmap(QPixmap())


class CollapsibleGroup(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.setCheckable(True)
        self.setChecked(True)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QGroupBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #666;
                border-radius: 2px;
                background: #2a2a2a;
            }
            QGroupBox::indicator:checked {
                background: #666;
            }
        """)


class VKTrackModifier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_files = []
        self.tracks_info = []
        self.output_dir = ""
        self.current_track_index = -1
        self.ffmpeg_available = self._check_ffmpeg()
        self.extra_track_path = ""
        self._load_config()
        self._init_ui()

    def _check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, encoding='utf-8', errors='ignore')
            return True
        except:
            pass
        
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
            ffmpeg_path = os.path.join(app_path, 'ffmpeg.exe')
            if os.path.exists(ffmpeg_path):
                try:
                    subprocess.run([ffmpeg_path, '-version'], capture_output=True, check=True, encoding='utf-8', errors='ignore')
                    os.environ['PATH'] = app_path + os.pathsep + os.environ.get('PATH', '')
                    return True
                except:
                    pass
        
        return False

    def _load_config(self):
        self.config = {
            'output_dir': '',
            'pitch_value': 1,
            'silence_duration': 45,
            'speed_value': 1.01,
            'eq_value': 3,
            'quality': '2',
            'preserve_metadata': True,
            'preserve_cover': True
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except:
                pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _init_ui(self):
        self.setWindowTitle("VK Track Modifier")
        self.setGeometry(100, 100, 1400, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self._init_left_panel(layout)
        self._init_right_panel(layout)

        self.method_merge.toggled.connect(self._on_merge_toggled)

        if not self.ffmpeg_available:
            self._show_ffmpeg_warning()

        self._load_settings_from_config()
        self._apply_preset('enhanced')

    def _init_left_panel(self, parent_layout):
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_panel.setMinimumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_title = QLabel("Файлы")
        left_title.setStyleSheet("font-size: 12px; font-weight: bold; padding: 6px; background: #2a2a2a; border-radius: 3px;")
        left_layout.addWidget(left_title)

        list_buttons = QHBoxLayout()
        list_buttons.setSpacing(5)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self._add_files)
        self.btn_add.setMinimumHeight(35)
        self.btn_add.setStyleSheet(self._get_button_style())

        self.btn_remove = QPushButton("Удалить")
        self.btn_remove.clicked.connect(self._remove_current_file)
        self.btn_remove.setMinimumHeight(35)
        self.btn_remove.setEnabled(False)
        self.btn_remove.setStyleSheet(self._get_button_style())

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self._clear_files)
        self.btn_clear.setMinimumHeight(35)
        self.btn_clear.setStyleSheet(self._get_button_style())

        list_buttons.addWidget(self.btn_add)
        list_buttons.addWidget(self.btn_remove)
        list_buttons.addWidget(self.btn_clear)
        left_layout.addLayout(list_buttons)

        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.currentRowChanged.connect(self._on_file_selected)
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #555;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        left_layout.addWidget(self.file_list)

        self.stats_label = QLabel("Файлов: 0 | Размер: 0 MB")
        self.stats_label.setStyleSheet("padding: 6px; background-color: #2a2a2a; border-radius: 3px;")
        left_layout.addWidget(self.stats_label)

        parent_layout.addWidget(left_panel)

    def _init_right_panel(self, parent_layout):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        self._init_cover_section(scroll_layout)
        self._init_metadata_section(scroll_layout)
        self._init_presets_section(scroll_layout)
        self._init_basic_params_section(scroll_layout)
        self._init_advanced_params_section(scroll_layout)
        self._init_technical_section(scroll_layout)
        self._init_quality_section(scroll_layout)
        self._init_info_section(scroll_layout)

        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        self._init_bottom_panel(right_layout)
        self._init_progress_bar(right_layout)

        parent_layout.addWidget(right_panel, 2)

    def _init_cover_section(self, layout):
        cover_group = CollapsibleGroup("ОБЛОЖКА")
        cover_layout = QHBoxLayout()
        cover_layout.setSpacing(12)

        self.cover_preview = CoverPreviewLabel()
        self.cover_preview.clicked.connect(self._select_cover)
        cover_layout.addWidget(self.cover_preview)

        cover_buttons = QVBoxLayout()
        cover_buttons.setSpacing(6)

        self.btn_cover = QPushButton("Выбрать обложку")
        self.btn_cover.clicked.connect(self._select_cover)
        self.btn_cover.setMinimumHeight(38)
        self.btn_cover.setStyleSheet(self._get_button_style())

        self.btn_cover_remove = QPushButton("Удалить")
        self.btn_cover_remove.clicked.connect(self._remove_cover)
        self.btn_cover_remove.setMinimumHeight(38)
        self.btn_cover_remove.setEnabled(False)
        self.btn_cover_remove.setStyleSheet(self._get_button_style())

        self.btn_cover_random = QPushButton("Случайная")
        self.btn_cover_random.clicked.connect(self._random_cover)
        self.btn_cover_random.setMinimumHeight(38)
        self.btn_cover_random.setStyleSheet(self._get_button_style())

        self.cover_info = QLabel("Нет обложки")
        self.cover_info.setWordWrap(True)
        self.cover_info.setAlignment(Qt.AlignCenter)
        self.cover_info.setStyleSheet("color: #888; padding: 4px;")

        cover_buttons.addWidget(self.btn_cover)
        cover_buttons.addWidget(self.btn_cover_remove)
        cover_buttons.addWidget(self.btn_cover_random)
        cover_buttons.addWidget(self.cover_info)
        cover_layout.addLayout(cover_buttons)

        cover_group.setLayout(cover_layout)
        layout.addWidget(cover_group)

    def _init_metadata_section(self, layout):
        meta_group = CollapsibleGroup("МЕТАДАННЫЕ")
        meta_layout = QGridLayout()
        meta_layout.setSpacing(6)

        meta_layout.addWidget(QLabel("Название:"), 0, 0)
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Оставить оригинал")
        self.edit_title.setMinimumHeight(32)
        meta_layout.addWidget(self.edit_title, 0, 1)

        meta_layout.addWidget(QLabel("Исполнитель:"), 1, 0)
        self.edit_artist = QLineEdit()
        self.edit_artist.setPlaceholderText("Оставить оригинал")
        self.edit_artist.setMinimumHeight(32)
        meta_layout.addWidget(self.edit_artist, 1, 1)

        meta_layout.addWidget(QLabel("Альбом:"), 2, 0)
        self.edit_album = QLineEdit()
        self.edit_album.setPlaceholderText("Оставить оригинал")
        self.edit_album.setMinimumHeight(32)
        meta_layout.addWidget(self.edit_album, 2, 1)

        meta_layout.addWidget(QLabel("Год:"), 3, 0)
        self.edit_year = QLineEdit()
        self.edit_year.setPlaceholderText("2024")
        self.edit_year.setMinimumHeight(32)
        meta_layout.addWidget(self.edit_year, 3, 1)

        meta_layout.addWidget(QLabel("Жанр:"), 4, 0)
        self.edit_genre = QLineEdit()
        self.edit_genre.setPlaceholderText("Pop, Rock...")
        self.edit_genre.setMinimumHeight(32)
        meta_layout.addWidget(self.edit_genre, 4, 1)

        meta_buttons = QHBoxLayout()
        meta_buttons.setSpacing(6)

        self.btn_meta_clear = QPushButton("Очистить")
        self.btn_meta_clear.clicked.connect(self._clear_meta_fields)
        self.btn_meta_clear.setMinimumHeight(32)
        self.btn_meta_clear.setStyleSheet(self._get_button_style())

        self.btn_meta_copy = QPushButton("Из оригинала")
        self.btn_meta_copy.clicked.connect(self._copy_meta_from_original)
        self.btn_meta_copy.setMinimumHeight(32)
        self.btn_meta_copy.setStyleSheet(self._get_button_style())

        self.btn_meta_random = QPushButton("Случайные")
        self.btn_meta_random.clicked.connect(self._random_metadata)
        self.btn_meta_random.setMinimumHeight(32)
        self.btn_meta_random.setStyleSheet(self._get_button_style())

        meta_buttons.addWidget(self.btn_meta_clear)
        meta_buttons.addWidget(self.btn_meta_copy)
        meta_buttons.addWidget(self.btn_meta_random)
        meta_layout.addLayout(meta_buttons, 5, 0, 1, 2)

        self.chk_reupload = QCheckBox("Добавить (REUPLOAD) к названию")
        self.chk_reupload.setChecked(False)
        meta_layout.addWidget(self.chk_reupload, 6, 0, 1, 2)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

    def _init_presets_section(self, layout):
        presets_group = CollapsibleGroup("ПРОФИЛИ ОБРАБОТКИ")
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)

        self.btn_preset_enhanced = QPushButton("Расширенный")
        self.btn_preset_enhanced.clicked.connect(lambda: self._apply_preset('enhanced'))
        self.btn_preset_enhanced.setMinimumHeight(38)
        self.btn_preset_enhanced.setStyleSheet(self._get_button_style())

        self.btn_preset_reupload = QPushButton("Reupload")
        self.btn_preset_reupload.clicked.connect(lambda: self._apply_preset('reupload'))
        self.btn_preset_reupload.setMinimumHeight(38)
        self.btn_preset_reupload.setStyleSheet(self._get_button_style())

        presets_layout.addWidget(self.btn_preset_enhanced)
        presets_layout.addWidget(self.btn_preset_reupload)
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

    def _init_basic_params_section(self, layout):
        basic_group = CollapsibleGroup("ОСНОВНЫЕ ПАРАМЕТРЫ")
        basic_layout = QGridLayout()
        basic_layout.setSpacing(6)

        self.method_pitch = QCheckBox("Изменить тональность")
        self.method_pitch.setChecked(True)
        basic_layout.addWidget(self.method_pitch, 0, 0)

        self.pitch_combo = QComboBox()
        self.pitch_combo.addItems(["-2 полутона", "-1 полутон", "+1 полутон", "+2 полутона", "Микро -0.5", "Микро +0.5"])
        self.pitch_combo.setCurrentIndex(1)
        self.pitch_combo.setMinimumHeight(32)
        basic_layout.addWidget(self.pitch_combo, 0, 1)

        self.method_silence = QCheckBox("Добавить тишину")
        self.method_silence.setChecked(True)
        basic_layout.addWidget(self.method_silence, 1, 0)

        self.silence_spin = QSpinBox()
        self.silence_spin.setRange(10, 300)
        self.silence_spin.setValue(45)
        self.silence_spin.setSuffix(" сек")
        self.silence_spin.setMinimumHeight(32)
        basic_layout.addWidget(self.silence_spin, 1, 1)

        self.method_speed = QCheckBox("Изменить скорость")
        self.method_speed.setChecked(True)
        basic_layout.addWidget(self.method_speed, 2, 0)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.97x", "0.98x", "0.99x", "1.01x", "1.02x", "1.03x", "0.995x", "1.005x"])
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.setMinimumHeight(32)
        basic_layout.addWidget(self.speed_combo, 2, 1)

        self.method_eq = QCheckBox("Эквализация")
        self.method_eq.setChecked(True)
        basic_layout.addWidget(self.method_eq, 3, 0)

        self.eq_combo = QComboBox()
        self.eq_combo.addItems(["Слабая (-2dB)", "Средняя (-4dB)", "Сильная (-6dB)", "Средние частоты", "Высокие частоты"])
        self.eq_combo.setCurrentIndex(1)
        self.eq_combo.setMinimumHeight(32)
        basic_layout.addWidget(self.eq_combo, 3, 1)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

    def _init_advanced_params_section(self, layout):
        advanced_group = CollapsibleGroup("ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ")
        advanced_layout = QGridLayout()
        advanced_layout.setSpacing(6)

        self.method_trim_silence = QCheckBox("Обрезать тишину в начале")
        self.method_trim_silence.setChecked(True)
        advanced_layout.addWidget(self.method_trim_silence, 0, 0)

        self.trim_spin = QSpinBox()
        self.trim_spin.setRange(1, 30)
        self.trim_spin.setValue(5)
        self.trim_spin.setSuffix(" сек")
        self.trim_spin.setMinimumHeight(32)
        advanced_layout.addWidget(self.trim_spin, 0, 1)

        self.method_cut_fragment = QCheckBox("Вырезать фрагмент")
        self.method_cut_fragment.setChecked(False)
        advanced_layout.addWidget(self.method_cut_fragment, 1, 0)

        self.cut_position_spin = QSpinBox()
        self.cut_position_spin.setRange(0, 99)
        self.cut_position_spin.setValue(50)
        self.cut_position_spin.setSuffix("% позиции")
        self.cut_position_spin.setMinimumHeight(32)
        advanced_layout.addWidget(self.cut_position_spin, 1, 1)

        self.cut_duration_spin = QSpinBox()
        self.cut_duration_spin.setRange(1, 10)
        self.cut_duration_spin.setValue(2)
        self.cut_duration_spin.setSuffix(" сек")
        self.cut_duration_spin.setMinimumHeight(32)
        advanced_layout.addWidget(QLabel("Длительность:"), 2, 0)
        advanced_layout.addWidget(self.cut_duration_spin, 2, 1)

        self.method_fade_out = QCheckBox("Плавное затухание")
        self.method_fade_out.setChecked(False)
        advanced_layout.addWidget(self.method_fade_out, 3, 0)

        self.fade_duration_spin = QSpinBox()
        self.fade_duration_spin.setRange(1, 30)
        self.fade_duration_spin.setValue(5)
        self.fade_duration_spin.setSuffix(" сек")
        self.fade_duration_spin.setMinimumHeight(32)
        advanced_layout.addWidget(self.fade_duration_spin, 3, 1)

        self.method_phase = QCheckBox("Фазовый сдвиг")
        self.method_phase.setChecked(True)
        advanced_layout.addWidget(self.method_phase, 4, 0)

        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["Слабый (0.3)", "Средний (0.5)", "Сильный (0.8)"])
        self.phase_combo.setCurrentIndex(1)
        self.phase_combo.setMinimumHeight(32)
        advanced_layout.addWidget(self.phase_combo, 4, 1)

        self.method_noise = QCheckBox("Добавить шум")
        self.method_noise.setChecked(True)
        advanced_layout.addWidget(self.method_noise, 5, 0)

        self.noise_combo = QComboBox()
        self.noise_combo.addItems(["Минимальный", "Слабый", "Средний"])
        self.noise_combo.setCurrentIndex(0)
        self.noise_combo.setMinimumHeight(32)
        advanced_layout.addWidget(self.noise_combo, 5, 1)

        self.method_compression = QCheckBox("Компрессия")
        self.method_compression.setChecked(True)
        advanced_layout.addWidget(self.method_compression, 6, 0)

        self.method_ultrasound = QCheckBox("Ультразвуковой шум (20-22kHz)")
        self.method_ultrasound.setChecked(True)
        advanced_layout.addWidget(self.method_ultrasound, 7, 0)

        self.method_dc_shift = QCheckBox("DC сдвиг")
        self.method_dc_shift.setChecked(True)
        advanced_layout.addWidget(self.method_dc_shift, 8, 0)

        self.method_merge = QCheckBox("Сращивание с другим треком")
        self.method_merge.setChecked(False)
        advanced_layout.addWidget(self.method_merge, 9, 0)

        self.btn_merge_track = QPushButton("Выбрать трек")
        self.btn_merge_track.clicked.connect(self._select_merge_track)
        self.btn_merge_track.setEnabled(False)
        self.btn_merge_track.setMinimumHeight(32)
        self.btn_merge_track.setStyleSheet(self._get_button_style())
        advanced_layout.addWidget(self.btn_merge_track, 9, 1)

        self.merge_track_label = QLabel("")
        self.merge_track_label.setStyleSheet("color: #888; font-style: italic;")
        advanced_layout.addWidget(self.merge_track_label, 10, 0, 1, 2)

        self.method_broken_duration = QCheckBox("Модифицировать длительность")
        self.method_broken_duration.setChecked(False)
        self.method_broken_duration.setToolTip("Создаёт конфликт длительности для сбоя парсинга")
        advanced_layout.addWidget(self.method_broken_duration, 11, 0)

        self.broken_type_combo = QComboBox()
        self.broken_type_combo.addItems([
            "1:04:19 (классический)",
            "Смещение +1 час",
            "Смещение x15",
            "Фейковый Xing"
        ])
        self.broken_type_combo.setCurrentIndex(0)
        self.broken_type_combo.setMinimumHeight(32)
        advanced_layout.addWidget(self.broken_type_combo, 11, 1)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

    def _init_technical_section(self, layout):
        extra_group = CollapsibleGroup("ТЕХНИЧЕСКИЕ НАСТРОЙКИ")
        extra_layout = QGridLayout()
        extra_layout.setSpacing(6)

        self.method_bitrate_jitter = QCheckBox("Изменение битрейта")
        self.method_bitrate_jitter.setChecked(True)
        extra_layout.addWidget(self.method_bitrate_jitter, 0, 0)

        self.method_frame_shift = QCheckBox("Сдвиг MP3 фреймов")
        self.method_frame_shift.setChecked(True)
        extra_layout.addWidget(self.method_frame_shift, 0, 1)

        self.method_fake_metadata = QCheckBox("Фальшивые метаданные")
        self.method_fake_metadata.setChecked(True)
        extra_layout.addWidget(self.method_fake_metadata, 1, 0)

        self.method_reorder_tags = QCheckBox("Переупорядочить ID3 теги")
        self.method_reorder_tags.setChecked(True)
        extra_layout.addWidget(self.method_reorder_tags, 1, 1)

        extra_group.setLayout(extra_layout)
        layout.addWidget(extra_group)

    def _init_quality_section(self, layout):
        quality_group = CollapsibleGroup("НАСТРОЙКИ КАЧЕСТВА")
        quality_layout = QGridLayout()
        quality_layout.setSpacing(6)

        quality_layout.addWidget(QLabel("Качество MP3:"), 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["320 kbps", "245 kbps (рекомендуется)", "175 kbps", "130 kbps"])
        self.quality_combo.setCurrentIndex(1)
        self.quality_combo.setMinimumHeight(32)
        quality_layout.addWidget(self.quality_combo, 0, 1)

        self.chk_preserve_meta = QCheckBox("Сохранить оригинальные метаданные")
        self.chk_preserve_meta.setChecked(True)
        quality_layout.addWidget(self.chk_preserve_meta, 1, 0, 1, 2)

        self.chk_preserve_cover = QCheckBox("Сохранить оригинальную обложку")
        self.chk_preserve_cover.setChecked(True)
        quality_layout.addWidget(self.chk_preserve_cover, 2, 0, 1, 2)

        self.chk_rename = QCheckBox("Переименовывать файлы (VK_001_title.mp3)")
        self.chk_rename.setChecked(True)
        quality_layout.addWidget(self.chk_rename, 3, 0, 1, 2)

        self.chk_delete_original = QCheckBox("Удалять оригиналы после обработки")
        self.chk_delete_original.setChecked(False)
        quality_layout.addWidget(self.chk_delete_original, 4, 0, 1, 2)

        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

    def _init_info_section(self, layout):
        info_group = CollapsibleGroup("ИНФОРМАЦИЯ О ТРЕКЕ")
        info_layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 6px;
            }
        """)
        info_layout.addWidget(self.info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def _init_bottom_panel(self, layout):
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setSpacing(10)
        bottom_layout.setContentsMargins(0, 8, 0, 0)

        self.btn_output = QPushButton("Папка вывода")
        self.btn_output.clicked.connect(self._select_output_dir)
        self.btn_output.setMinimumHeight(42)
        self.btn_output.setStyleSheet(self._get_button_style())

        self.btn_preview = QPushButton("Предпросмотр (15 сек)")
        self.btn_preview.clicked.connect(self._preview_effects)
        self.btn_preview.setMinimumHeight(42)
        self.btn_preview.setStyleSheet(self._get_button_style())

        self.btn_start = QPushButton("ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.clicked.connect(self._start_modification)
        self.btn_start.setMinimumHeight(48)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #5a5a5a;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #6a6a6a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #666;
            }
        """)

        bottom_layout.addWidget(self.btn_output)
        bottom_layout.addWidget(self.btn_preview)
        bottom_layout.addWidget(self.btn_start, 2)

        layout.addWidget(bottom_panel)

    def _init_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #666;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def _get_button_style(self):
        return """
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #555;
                border-color: #444;
            }
        """

    def _on_merge_toggled(self, checked):
        self.btn_merge_track.setEnabled(checked)
        if not checked:
            self.extra_track_path = ""
            self.merge_track_label.setText("")

    def _select_merge_track(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите трек для сращивания", "", "MP3 files (*.mp3)"
        )
        if file_path:
            self.extra_track_path = file_path
            self.merge_track_label.setText(f"Выбран: {os.path.basename(file_path)}")

    def _random_cover(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        pixmap = QPixmap(500, 500)
        pixmap.fill(QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))

        temp_cover = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        pixmap.save(temp_cover.name)
        temp_cover.close()

        track = self.tracks_info[self.current_track_index]
        with open(temp_cover.name, 'rb') as f:
            track.cover_data = f.read()
        track.cover_mime = 'image/png'

        self.cover_preview.set_pixmap(pixmap)
        self.cover_info.setText("Случайная обложка")
        self.btn_cover_remove.setEnabled(True)

        try:
            os.unlink(temp_cover.name)
        except:
            pass

    def _random_metadata(self):
        titles = ["Track", "Song", "Melody", "Rhythm", "Harmony", "Beat", "Flow", "Vibe", "Sound", "Wave"]
        artists = ["Artist", "Musician", "Producer", "DJ", "Band", "Project", "Studio", "Creator"]
        albums = ["Album", "Collection", "Mix", "Set", "Compilation", "Series", "Volume"]
        genres = ["Pop", "Rock", "Electronic", "Hip Hop", "Jazz", "Classical", "Ambient", "Dance"]

        self.edit_title.setText(f"{random.choice(titles)} {random.randint(1, 999)}")
        self.edit_artist.setText(f"{random.choice(artists)} {random.randint(1, 99)}")
        self.edit_album.setText(f"{random.choice(albums)} {random.randint(2020, 2024)}")
        self.edit_year.setText(str(random.randint(2000, 2024)))
        self.edit_genre.setText(random.choice(genres))

    def _preview_effects(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        settings = self._get_settings()
        track = self.tracks_info[self.current_track_index]

        temp_preview = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_preview.close()

        filters = self._build_filters(settings)

        cmd = ['ffmpeg', '-i', track.file_path, '-t', '15']
        if filters:
            cmd.extend(['-af', filters])
        cmd.extend(['-codec:a', 'libmp3lame', '-q:a', '2', '-y', temp_preview.name])

        try:
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                if sys.platform == 'win32':
                    os.startfile(temp_preview.name)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', temp_preview.name])
                else:
                    subprocess.run(['xdg-open', temp_preview.name])
                QTimer.singleShot(60000, lambda: self._delete_temp_file(temp_preview.name))
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка создания предпросмотра:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_temp_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass

    def _show_ffmpeg_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("FFmpeg не найден")
        msg.setText("Для работы программы требуется FFmpeg")
        msg.setInformativeText("Скачайте FFmpeg с ffmpeg.org и добавьте в PATH")
        msg.exec_()
        self.btn_start.setEnabled(False)

    def _load_settings_from_config(self):
        self.output_dir = self.config.get('output_dir', '')
        if self.output_dir:
            self.btn_output.setText(f"Папка: {os.path.basename(self.output_dir)}")
        self.chk_preserve_meta.setChecked(self.config.get('preserve_metadata', True))
        self.chk_preserve_cover.setChecked(self.config.get('preserve_cover', True))

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите MP3 файлы", "", "MP3 files (*.mp3)"
        )
        if not files:
            return

        for file_path in files:
            if file_path not in self.input_files:
                self.input_files.append(file_path)
                track = TrackInfo(file_path)
                with open(file_path, 'rb') as f:
                    track.file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                self.tracks_info.append(track)
                self.file_list.addItem(f"{os.path.basename(file_path)}\n{track.size_mb:.1f} MB")

        self._update_stats()
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.btn_remove.setEnabled(True)

    def _remove_current_file(self):
        current = self.file_list.currentRow()
        if current >= 0:
            self.input_files.pop(current)
            self.tracks_info.pop(current)
            self.file_list.takeItem(current)
            self._update_stats()
            if self.file_list.count() == 0:
                self.btn_remove.setEnabled(False)
                self._clear_editor()

    def _clear_files(self):
        self.input_files.clear()
        self.tracks_info.clear()
        self.file_list.clear()
        self._update_stats()
        self.btn_remove.setEnabled(False)
        self._clear_editor()

    def _clear_editor(self):
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()
        self.cover_preview.set_pixmap(None)
        self.cover_info.setText("Нет обложки")
        self.info_text.clear()

    def _on_file_selected(self, index):
        if index < 0 or index >= len(self.tracks_info):
            return

        self.current_track_index = index
        track = self.tracks_info[index]
        self._load_metadata(track)

        info = f"Файл: {track.file_name}\n"
        info += f"Размер: {track.size_mb:.2f} MB\n"
        info += f"MD5: {track.file_hash}\n"
        if track.duration_sec > 0:
            info += f"Длительность: {str(timedelta(seconds=int(track.duration_sec)))}\n"
        if track.artist or track.title:
            info += f"Оригинал: {track.artist} - {track.title}"

        self.info_text.setText(info)
        self._extract_cover(track)

    def _load_metadata(self, track):
        try:
            audio = MP3(track.file_path)
            track.duration_sec = audio.info.length
            track.bitrate = audio.info.bitrate
            track.sample_rate = audio.info.sample_rate

            if audio.tags:
                if 'TIT2' in audio.tags:
                    track.title = str(audio.tags['TIT2'])
                if 'TPE1' in audio.tags:
                    track.artist = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    track.album = str(audio.tags['TALB'])
                if 'TDRC' in audio.tags:
                    track.year = str(audio.tags['TDRC'])
                if 'TCON' in audio.tags:
                    track.genre = str(audio.tags['TCON'])
        except Exception as e:
            print(f"Error loading metadata: {e}")

    def _extract_cover(self, track):
        try:
            audio = MP3(track.file_path)
            if audio.tags:
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        track.cover_data = tag.data
                        track.cover_mime = tag.mime
                        pixmap = QPixmap()
                        pixmap.loadFromData(tag.data)
                        self.cover_preview.set_pixmap(pixmap)
                        self.cover_info.setText("Оригинальная обложка")
                        self.btn_cover_remove.setEnabled(True)
                        return

            self.cover_preview.set_pixmap(None)
            track.cover_data = None
            self.cover_info.setText("Нет обложки")
            self.btn_cover_remove.setEnabled(False)
        except Exception as e:
            print(f"Error extracting cover: {e}")

    def _select_cover(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            track = self.tracks_info[self.current_track_index]
            with open(file_path, 'rb') as f:
                track.cover_data = f.read()
            ext = os.path.splitext(file_path)[1].lower()
            track.cover_mime = 'image/png' if ext == '.png' else 'image/jpeg'
            pixmap = QPixmap(file_path)
            self.cover_preview.set_pixmap(pixmap)
            self.cover_info.setText(f"Обложка: {os.path.basename(file_path)}")
            self.btn_cover_remove.setEnabled(True)

    def _remove_cover(self):
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            track.cover_data = None
            self._extract_cover(track)

    def _copy_meta_from_original(self):
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            self.edit_title.setText(track.title)
            self.edit_artist.setText(track.artist)
            self.edit_album.setText(track.album)
            self.edit_year.setText(track.year)
            self.edit_genre.setText(track.genre)

    def _clear_meta_fields(self):
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()

    def _update_stats(self):
        count = len(self.input_files)
        total_size = sum(os.path.getsize(f) for f in self.input_files) / (1024 * 1024)
        self.stats_label.setText(f"Файлов: {count} | Размер: {total_size:.1f} MB")

    def _apply_preset(self, preset):
        if preset == 'enhanced':
            self.method_trim_silence.setChecked(False)
            self.method_cut_fragment.setChecked(False)
            self.method_fade_out.setChecked(False)
            self.method_broken_duration.setChecked(True)
            self.broken_type_combo.setCurrentIndex(0)
            self.method_pitch.setChecked(False)
            self.method_silence.setChecked(False)
            self.method_speed.setChecked(True)
            self.speed_combo.setCurrentIndex(3)
            self.method_eq.setChecked(False)
            self.method_phase.setChecked(False)
            self.method_noise.setChecked(False)
            self.method_compression.setChecked(False)
            self.method_ultrasound.setChecked(False)
            self.method_dc_shift.setChecked(False)
            self.method_merge.setChecked(False)
            self.method_bitrate_jitter.setChecked(True)
            self.method_frame_shift.setChecked(False)
            self.method_fake_metadata.setChecked(True)
            self.method_reorder_tags.setChecked(True)
            self.chk_reupload.setChecked(True)
            self.quality_combo.setCurrentIndex(0)
            self.chk_rename.setChecked(False)
            self.chk_preserve_meta.setChecked(False)
            self.chk_preserve_cover.setChecked(False)

        elif preset == 'reupload':
            self.method_trim_silence.setChecked(False)
            self.method_cut_fragment.setChecked(False)
            self.method_fade_out.setChecked(False)
            self.method_broken_duration.setChecked(True)
            self.broken_type_combo.setCurrentIndex(1)
            self.method_pitch.setChecked(False)
            self.method_silence.setChecked(False)
            self.method_speed.setChecked(False)
            self.method_eq.setChecked(False)
            self.method_phase.setChecked(False)
            self.method_noise.setChecked(False)
            self.method_compression.setChecked(False)
            self.method_ultrasound.setChecked(False)
            self.method_dc_shift.setChecked(False)
            self.method_merge.setChecked(False)
            self.method_bitrate_jitter.setChecked(False)
            self.method_frame_shift.setChecked(False)
            self.method_fake_metadata.setChecked(False)
            self.method_reorder_tags.setChecked(False)
            self.chk_reupload.setChecked(True)
            self.quality_combo.setCurrentIndex(0)

    def _select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", self.config.get('output_dir', '')
        )
        if directory:
            self.output_dir = directory
            self.config['output_dir'] = directory
            self.btn_output.setText(f"Папка: {os.path.basename(directory)}")
            self._save_config()

    def _get_settings(self):
        quality_map = {0: '0', 1: '2', 2: '5', 3: '7'}
        pitch_values = [-2, -1, 1, 2, -0.5, 0.5]
        speed_values = [0.97, 0.98, 0.99, 1.01, 1.02, 1.03, 0.995, 1.005]
        eq_values = [2, 4, 6, 4, -3]
        phase_values = [0.3, 0.5, 0.8]
        noise_values = [0.0005, 0.001, 0.002]

        settings = {
            'methods': {
                'trim_silence': self.method_trim_silence.isChecked(),
                'cut_fragment': self.method_cut_fragment.isChecked(),
                'fade_out': self.method_fade_out.isChecked(),
                'broken_duration': self.method_broken_duration.isChecked(),
                'pitch': self.method_pitch.isChecked(),
                'silence': self.method_silence.isChecked(),
                'speed': self.method_speed.isChecked(),
                'eq': self.method_eq.isChecked(),
                'phase': self.method_phase.isChecked(),
                'noise': self.method_noise.isChecked(),
                'compression': self.method_compression.isChecked(),
                'ultrasound': self.method_ultrasound.isChecked(),
                'dc_shift': self.method_dc_shift.isChecked(),
                'merge': self.method_merge.isChecked(),
                'bitrate_jitter': self.method_bitrate_jitter.isChecked(),
                'frame_shift': self.method_frame_shift.isChecked(),
                'fake_metadata': self.method_fake_metadata.isChecked(),
                'reorder_tags': self.method_reorder_tags.isChecked()
            },
            'broken_type': self.broken_type_combo.currentIndex(),
            'trim_duration': self.trim_spin.value(),
            'cut_position_percent': self.cut_position_spin.value(),
            'cut_duration': self.cut_duration_spin.value(),
            'fade_duration': self.fade_duration_spin.value(),
            'pitch_value': pitch_values[self.pitch_combo.currentIndex()],
            'silence_duration': self.silence_spin.value(),
            'speed_value': speed_values[self.speed_combo.currentIndex()],
            'eq_value': eq_values[self.eq_combo.currentIndex()],
            'eq_type': self.eq_combo.currentIndex(),
            'phase_value': phase_values[self.phase_combo.currentIndex()],
            'noise_value': noise_values[self.noise_combo.currentIndex()],
            'quality': quality_map[self.quality_combo.currentIndex()],
            'preserve_metadata': self.chk_preserve_meta.isChecked(),
            'preserve_cover': self.chk_preserve_cover.isChecked(),
            'rename_files': self.chk_rename.isChecked(),
            'delete_original': self.chk_delete_original.isChecked(),
            'reupload': self.chk_reupload.isChecked(),
            'extra_track_path': self.extra_track_path if self.method_merge.isChecked() else ""
        }

        self.config['pitch_value'] = settings['pitch_value']
        self.config['silence_duration'] = settings['silence_duration']
        self.config['speed_value'] = settings['speed_value']
        self.config['eq_value'] = settings['eq_value']
        self.config['quality'] = settings['quality']
        self.config['preserve_metadata'] = settings['preserve_metadata']
        self.config['preserve_cover'] = settings['preserve_cover']
        self._save_config()

        return settings

    def _build_filters(self, settings):
        filters = []

        if settings['methods']['pitch']:
            semitones = settings['pitch_value']
            rate = 44100 * (2 ** (semitones / 12))
            filters.append(f"asetrate={rate:.0f},aresample=44100")

        if settings['methods']['speed']:
            filters.append(f"atempo={settings['speed_value']}")

        if settings['methods']['eq']:
            if settings['eq_type'] == 3:
                filters.append("equalizer=f=1000:width_type=o:width=2:g=-4")
                filters.append("equalizer=f=2000:width_type=o:width=2:g=-2")
            elif settings['eq_type'] == 4:
                filters.append("equalizer=f=8000:width_type=o:width=2:g=3")
            else:
                filters.append(f"equalizer=f=1000:width_type=o:width=2:g={-settings['eq_value']}")

        if settings['methods']['phase']:
            delay = settings['phase_value']
            filters.append(f"aphaser=type=t:delay={delay}:decay=0.4")

        if settings['methods']['noise']:
            noise_level = settings['noise_value']
            threshold = 1.0 - (noise_level * 200)
            filters.append(f"asoftclip=type=3:threshold={threshold}")

        if settings['methods']['compression']:
            filters.append("compand=attacks=0.1:decays=0.1:points=-80/-80|-45/-15|-27/-9|0/-7|20/-7")

        if settings['methods']['ultrasound']:
            filters.append("earwax")

        if settings['methods']['dc_shift']:
            filters.append("dcshift=0.001")

        if settings['methods']['silence']:
            filters.append(f"apad=pad_dur={settings['silence_duration']}")

        return ",".join(filters) if filters else None

    def _start_modification(self):
        if not self.input_files:
            QMessageBox.warning(self, "Внимание", "Добавьте файлы для обработки!")
            return

        if not self.output_dir:
            reply = QMessageBox.question(
                self, "Папка не выбрана",
                "Использовать папку исходных файлов для сохранения?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.output_dir = os.path.dirname(self.input_files[0])
            else:
                return

        os.makedirs(self.output_dir, exist_ok=True)
        settings = self._get_settings()

        if settings['methods']['merge'] and not settings['extra_track_path']:
            QMessageBox.warning(self, "Внимание", "Выбран метод сращивания, но не выбран трек!")
            return

        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.input_files))
        self.progress_bar.setValue(0)

        self.worker = ModificationWorker(
            self.input_files,
            self.tracks_info,
            self.output_dir,
            settings,
            {
                'title': self.edit_title.text(),
                'artist': self.edit_artist.text(),
                'album': self.edit_album.text(),
                'year': self.edit_year.text(),
                'genre': self.edit_genre.text()
            }
        )
        self.worker.progress_update.connect(self._update_progress)
        self.worker.file_complete.connect(self._on_file_complete)
        self.worker.all_complete.connect(self._on_all_complete)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _set_ui_enabled(self, enabled):
        self.btn_add.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled and self.file_list.count() > 0)
        self.btn_clear.setEnabled(enabled)
        self.btn_start.setEnabled(enabled)
        self.btn_output.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

    def _update_progress(self, current, total, file_name):
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Обработка {current}/{total}: {os.path.basename(file_name)}")

    def _on_file_complete(self, file_name, success, output_path):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if file_name in item.text():
                if success:
                    item.setText(f"[OK] {os.path.basename(file_name)}")
                else:
                    item.setText(f"[ERR] {os.path.basename(file_name)}")
                break

    def _on_all_complete(self, success_count, total_count):
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)

        if success_count == total_count:
            QMessageBox.information(
                self, "Готово",
                f"Все {total_count} треков успешно обработаны!\n\n"
                f"Сохранено в:\n{self.output_dir}"
            )
        else:
            QMessageBox.warning(
                self, "Обработка завершена",
                f"Успешно: {success_count} из {total_count}\n"
                f"Ошибок: {total_count - success_count}"
            )

        try:
            if sys.platform == 'win32':
                os.startfile(self.output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.output_dir])
            else:
                subprocess.run(['xdg-open', self.output_dir])
        except:
            pass

    def _on_error(self, error_msg):
        QMessageBox.critical(self, "Ошибка", error_msg)


class ModificationWorker(QThread):
    progress_update = pyqtSignal(int, int, str)
    file_complete = pyqtSignal(str, bool, str)
    all_complete = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, files, tracks_info, output_dir, settings, metadata):
        super().__init__()
        self.files = files
        self.tracks_info = tracks_info
        self.output_dir = output_dir
        self.settings = settings
        self.metadata = metadata

    def run(self):
        success_count = 0
        total = len(self.files)

        for i, (file_path, track_info) in enumerate(zip(self.files, self.tracks_info)):
            temp_files = []
            try:
                self.progress_update.emit(i + 1, total, file_path)

                if self.settings['rename_files']:
                    name, ext = os.path.splitext(os.path.basename(file_path))
                    output_file = os.path.join(self.output_dir, f"VK_{i+1:03d}_{name}.mp3")
                else:
                    name, ext = os.path.splitext(os.path.basename(file_path))
                    output_file = os.path.join(self.output_dir, f"modified_{name}.mp3")

                current_input = file_path

                if self.settings['methods'].get('trim_silence', False):
                    trim_dur = self.settings.get('trim_duration', 5)
                    trim_temp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    trim_temp.close()
                    temp_files.append(trim_temp.name)
                    cmd_trim = ['ffmpeg', '-i', current_input, '-ss', f'00:00:{trim_dur}', '-codec:a', 'copy', '-y', trim_temp.name]
                    subprocess.run(cmd_trim, capture_output=True, encoding='utf-8', errors='ignore')
                    current_input = trim_temp.name

                if self.settings['methods'].get('cut_fragment', False):
                    cut_pos_percent = self.settings.get('cut_position_percent', 50)
                    cut_dur = self.settings.get('cut_duration', 2)
                    try:
                        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                     '-of', 'default=noprint_wrappers=1:nokey=1', current_input]
                        result = subprocess.run(probe_cmd, capture_output=True, encoding='utf-8', errors='ignore')
                        duration = float(result.stdout.strip())
                        cut_start = (duration * cut_pos_percent / 100) - (cut_dur / 2)
                        if cut_start < 0:
                            cut_start = 0
                        cut_end = cut_start + cut_dur
                        cut_temp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                        cut_temp.close()
                        temp_files.append(cut_temp.name)
                        filter_cut = f"[0:a]atrim=0:{cut_start},asetpts=PTS-STARTPTS[f];[0:a]atrim={cut_end},asetpts=PTS-STARTPTS[s];[f][s]concat=n=2:v=0:a=1[out]"
                        cmd_cut = ['ffmpeg', '-i', current_input, '-filter_complex', filter_cut, '-map', '[out]', '-codec:a', 'libmp3lame', '-q:a', '2', '-y', cut_temp.name]
                        subprocess.run(cmd_cut, capture_output=True, encoding='utf-8', errors='ignore')
                        current_input = cut_temp.name
                    except Exception as e:
                        print(f"Error cutting fragment: {e}")

                if self.settings['methods'].get('merge', False) and self.settings.get('extra_track_path'):
                    concat_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                    concat_list.write(f"file '{current_input}'\n")
                    concat_list.write(f"file '{self.settings['extra_track_path']}'")
                    concat_list.close()
                    temp_files.append(concat_list.name)
                    merged_temp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    merged_temp.close()
                    temp_files.append(merged_temp.name)
                    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list.name,
                           '-codec:a', 'libmp3lame', '-q:a', self.settings['quality'],
                           '-y', merged_temp.name]
                    subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
                    current_input = merged_temp.name

                filters = self._build_filters()
                cmd = ['ffmpeg', '-i', current_input]

                if self.settings['methods'].get('fade_out', False):
                    fade_dur = self.settings.get('fade_duration', 5)
                    try:
                        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                     '-of', 'default=noprint_wrappers=1:nokey=1', current_input]
                        result = subprocess.run(probe_cmd, capture_output=True, encoding='utf-8', errors='ignore')
                        duration = float(result.stdout.strip())
                        fade_start = max(0, duration - fade_dur)
                        filters_list = filters.split(',') if filters else []
                        filters_list.append(f"afade=t=out:st={fade_start}:d={fade_dur}")
                        filters = ','.join(filters_list)
                    except:
                        pass

                cover_temp_path = None
                if track_info.cover_data:
                    cover_ext = track_info.cover_mime.split('/')[1] if '/' in track_info.cover_mime else 'jpg'
                    cover_temp = tempfile.NamedTemporaryFile(suffix=f'.{cover_ext}', delete=False)
                    cover_temp.write(track_info.cover_data)
                    cover_temp.close()
                    temp_files.append(cover_temp.name)
                    cover_temp_path = cover_temp.name
                    cmd.extend(['-i', cover_temp.name, '-map', '0:a', '-map', '1:v'])
                    cmd.extend(['-c:v', 'mjpeg', '-q:v', '2', '-disposition:v', 'attached_pic'])
                else:
                    cmd.extend(['-map', '0:a'])

                if filters:
                    cmd.extend(['-af', filters])

                # Определяем базовое название: из поля ввода или из оригинала
                if self.metadata['title']:
                    title_to_use = self.metadata['title']
                elif self.settings['preserve_metadata'] and track_info.title:
                    title_to_use = track_info.title
                else:
                    title_to_use = ""

                # Добавляем REUPLOAD если нужно
                if self.settings.get('reupload', False) and title_to_use:
                    title_to_use = f"{title_to_use} (REUPLOAD)"

                if title_to_use:
                    cmd.extend(['-metadata', f'title={title_to_use}'])

                if self.metadata['artist']:
                    cmd.extend(['-metadata', f'artist={self.metadata["artist"]}'])
                elif self.settings['preserve_metadata'] and track_info.artist:
                    cmd.extend(['-metadata', f'artist={track_info.artist}'])

                if self.metadata['album']:
                    cmd.extend(['-metadata', f'album={self.metadata["album"]}'])
                elif self.settings['preserve_metadata'] and track_info.album:
                    cmd.extend(['-metadata', f'album={track_info.album}'])

                if self.metadata['year']:
                    cmd.extend(['-metadata', f'date={self.metadata["year"]}'])
                elif self.settings['preserve_metadata'] and track_info.year:
                    cmd.extend(['-metadata', f'date={track_info.year}'])

                if self.metadata['genre']:
                    cmd.extend(['-metadata', f'genre={self.metadata["genre"]}'])
                elif self.settings['preserve_metadata'] and track_info.genre:
                    cmd.extend(['-metadata', f'genre={track_info.genre}'])

                if self.settings['methods'].get('fake_metadata', False):
                    fake_text = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ', k=random.randint(100, 500)))
                    cmd.extend(['-metadata', f'comment={fake_text}'])

                if self.settings['methods'].get('bitrate_jitter', False):
                    bitrate = random.choice([192, 224, 256, 320])
                    cmd.extend(['-codec:a', 'libmp3lame', '-b:a', f'{bitrate}k'])
                else:
                    cmd.extend(['-codec:a', 'libmp3lame', '-q:a', self.settings['quality']])

                if self.settings['methods'].get('frame_shift', False) and not self.settings['methods'].get('broken_duration', False):
                    cmd.extend(['-write_xing', '0'])

                cmd.extend(['-id3v2_version', '3', '-y', output_file])

                result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')

                if self.settings['methods'].get('reorder_tags', False) and os.path.exists(output_file):
                    try:
                        self._reorder_id3_tags(output_file)
                    except:
                        pass

                if self.settings['methods'].get('broken_duration', False) and os.path.exists(output_file):
                    try:
                        bug_type = self.settings.get('broken_type', 0)
                        self._apply_broken_duration(output_file, bug_type)
                    except:
                        pass

                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass

                if result.returncode == 0:
                    success_count += 1
                    self.file_complete.emit(file_path, True, output_file)
                    if self.settings.get('delete_original', False):
                        try:
                            os.unlink(file_path)
                        except:
                            pass
                else:
                    self.file_complete.emit(file_path, False, "")
                    print(f"FFmpeg error: {result.stderr}")

            except Exception as e:
                self.file_complete.emit(file_path, False, "")
                self.error_occurred.emit(f"Ошибка: {str(e)}")

        self.all_complete.emit(success_count, total)

    def _build_filters(self):
        filters = []
        if self.settings['methods'].get('pitch', False):
            semitones = self.settings['pitch_value']
            rate = 44100 * (2 ** (semitones / 12))
            filters.append(f"asetrate={rate:.0f},aresample=44100")
        if self.settings['methods'].get('speed', False):
            filters.append(f"atempo={self.settings['speed_value']}")
        if self.settings['methods'].get('eq', False):
            if self.settings.get('eq_type') == 3:
                filters.append("equalizer=f=1000:width_type=o:width=2:g=-4")
                filters.append("equalizer=f=2000:width_type=o:width=2:g=-2")
            elif self.settings.get('eq_type') == 4:
                filters.append("equalizer=f=8000:width_type=o:width=2:g=3")
            else:
                filters.append(f"equalizer=f=1000:width_type=o:width=2:g={-self.settings['eq_value']}")
        if self.settings['methods'].get('phase', False):
            delay = self.settings['phase_value']
            filters.append(f"aphaser=type=t:delay={delay}:decay=0.4")
        if self.settings['methods'].get('noise', False):
            noise_level = self.settings['noise_value']
            threshold = 1.0 - (noise_level * 200)
            filters.append(f"asoftclip=type=3:threshold={threshold}")
        if self.settings['methods'].get('compression', False):
            filters.append("compand=attacks=0.1:decays=0.1:points=-80/-80|-45/-15|-27/-9|0/-7|20/-7")
        if self.settings['methods'].get('ultrasound', False):
            filters.append("earwax")
        if self.settings['methods'].get('dc_shift', False):
            filters.append("dcshift=0.001")
        if self.settings['methods'].get('silence', False):
            filters.append(f"apad=pad_dur={self.settings['silence_duration']}")
        return ",".join(filters) if filters else None

    def _reorder_id3_tags(self, file_path):
        try:
            audio = MP3(file_path)
            if audio.tags:
                audio.tags.update_to_v23()
                audio.save()
        except:
            pass

    def _apply_broken_duration(self, file_path, bug_type):
        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())

            xing_pos = data.find(b'Xing')
            info_pos = data.find(b'Info')
            vbr_pos = xing_pos if xing_pos > 0 else info_pos

            if vbr_pos > 0 and vbr_pos < len(data) - 12:
                if bug_type == 0:
                    fake_frames = 0x00186A00
                    data[vbr_pos+8:vbr_pos+12] = fake_frames.to_bytes(4, 'big')
                elif bug_type == 1:
                    orig_frames = int.from_bytes(data[vbr_pos+8:vbr_pos+12], 'big')
                    fake_frames = orig_frames + 158760
                    data[vbr_pos+8:vbr_pos+12] = fake_frames.to_bytes(4, 'big')
                elif bug_type == 2:
                    orig_frames = int.from_bytes(data[vbr_pos+8:vbr_pos+12], 'big')
                    fake_frames = orig_frames * 15
                    data[vbr_pos+8:vbr_pos+12] = fake_frames.to_bytes(4, 'big')
                elif bug_type == 3:
                    data[vbr_pos:vbr_pos+4] = b'XXXX'
                    fake_frames = 0x0030D400
                    data[vbr_pos+8:vbr_pos+12] = fake_frames.to_bytes(4, 'big')

            with open(file_path, 'wb') as f:
                f.write(data)

            audio = MP3(file_path)
            if audio.tags:
                fake_tlen = 3859000
                audio.tags['TLEN'] = TLEN(encoding=3, text=str(fake_tlen))
                if bug_type == 3:
                    audio.tags['TXXX:BrokenVBR'] = TXXX(encoding=3, desc='BrokenVBR', text='true')
                audio.save()
        except Exception as e:
            print(f"Error applying broken duration: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    app.setPalette(dark_palette)

    window = VKTrackModifier()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
