#!/usr/bin/env python3
"""
VK Track Modifier - GUI приложение для обработки MP3 треков
Модульная версия с улучшенной структурой
"""

import sys
import os
import random
import subprocess
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

# Импорт из локальных модулей
# Определяем директорию текущего файла для корректного импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Добавляем parent_dir в sys.path для импорта пакета vk_modifier
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Пробуем импорт как пакет, затем как отдельные модули
try:
    from vk_modifier.models import TrackInfo, ProcessingSettings, Metadata
    from vk_modifier.processors import FilterBuilder, AudioProcessor
    from vk_modifier.utils import (
        ConfigManager, MetadataExtractor, PresetManager,
        check_ffmpeg, get_quality_map, get_pitch_values, get_speed_values,
        get_eq_values, get_phase_values, get_noise_values
    )
    from vk_modifier.ui import CoverPreviewLabel, CollapsibleGroup
except ImportError:
    try:
        from models import TrackInfo, ProcessingSettings, Metadata
        from processors import FilterBuilder, AudioProcessor
        from utils import (
            ConfigManager, MetadataExtractor, PresetManager,
            check_ffmpeg, get_quality_map, get_pitch_values, get_speed_values,
            get_eq_values, get_phase_values, get_noise_values
        )
        from ui import CoverPreviewLabel, CollapsibleGroup
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что запускаете скрипт из директории vk_modifier или установите пакет.")
        sys.exit(1)


CONFIG_FILE = "vk_modifier_config.json"


class ModificationWorker(QThread):
    """Worker поток для обработки файлов"""
    progress_update = pyqtSignal(int, int, str)
    file_complete = pyqtSignal(str, bool, str)
    all_complete = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        files: list,
        tracks_info: list,
        output_dir: str,
        settings: dict,
        metadata: dict
    ):
        super().__init__()
        self.files = files
        self.tracks_info = tracks_info
        self.output_dir = output_dir
        self.settings = settings
        self.metadata = metadata
        self.processor = AudioProcessor()

    def run(self):
        success_count = 0
        total = len(self.files)

        for i, (file_path, track_info) in enumerate(zip(self.files, self.tracks_info)):
            try:
                self.progress_update.emit(i + 1, total, file_path)

                # Определение пути выходного файла
                if self.settings['rename_files']:
                    name = os.path.splitext(os.path.basename(file_path))[0]
                    output_file = os.path.join(
                        self.output_dir, f"VK_{i+1:03d}_{name}.mp3"
                    )
                else:
                    name = os.path.splitext(os.path.basename(file_path))[0]
                    output_file = os.path.join(
                        self.output_dir, f"modified_{name}.mp3"
                    )

                # Подготовка обложки
                cover_temp_path = None
                if track_info.cover_data:
                    cover_ext = track_info.cover_mime.split('/')[1] \
                        if '/' in track_info.cover_mime else 'jpg'
                    cover_temp = tempfile.NamedTemporaryFile(
                        suffix=f'.{cover_ext}', delete=False
                    )
                    cover_temp.write(track_info.cover_data)
                    cover_temp.close()
                    cover_temp_path = cover_temp.name

                # Подготовка метаданных
                title_to_use = self._get_title_to_use(track_info)
                meta_dict = {
                    'title': title_to_use,
                    'artist': self.metadata.get('artist', '') or track_info.artist,
                    'album': self.metadata.get('album', '') or track_info.album,
                    'year': self.metadata.get('year', '') or track_info.year,
                    'genre': self.metadata.get('genre', '') or track_info.genre
                }

                # Обработка аудио
                success, error = self.processor.process_audio(
                    input_path=file_path,
                    output_path=output_file,
                    settings=self.settings,
                    cover_path=cover_temp_path,
                    metadata=meta_dict if any(meta_dict.values()) else None
                )

                # Очистка временной обложки
                if cover_temp_path and os.path.exists(cover_temp_path):
                    try:
                        os.unlink(cover_temp_path)
                    except Exception:
                        pass

                if success:
                    success_count += 1
                    self.file_complete.emit(file_path, True, output_file)

                    # Удаление оригинала если указано
                    if self.settings.get('delete_original', False):
                        try:
                            os.unlink(file_path)
                        except Exception:
                            pass
                else:
                    self.file_complete.emit(file_path, False, "")
                    print(f"Processing error: {error}")

            except Exception as e:
                self.file_complete.emit(file_path, False, "")
                self.error_occurred.emit(f"Ошибка: {str(e)}")

        self.all_complete.emit(success_count, total)

    def _get_title_to_use(self, track_info: TrackInfo) -> str:
        """Определяет название для использования"""
        if self.metadata.get('title'):
            title = self.metadata['title']
        elif self.settings.get('preserve_metadata', True) and track_info.title:
            title = track_info.title
        else:
            title = ""

        # Добавление REUPLOAD если нужно
        if self.settings.get('reupload', False) and title:
            title = f"{title} (REUPLOAD)"

        return title


class VKTrackModifier(QMainWindow):
    """Основное окно приложения"""

    def __init__(self):
        super().__init__()
        self.input_files = []
        self.tracks_info = []
        self.output_dir = ""
        self.current_track_index = -1
        self.ffmpeg_available = check_ffmpeg()
        self.extra_track_path = ""

        # Менеджеры
        self.config_manager = ConfigManager()
        self.config_manager.load()

        self._init_ui()

        # Подключение сигналов
        self.method_merge.toggled.connect(self._on_merge_toggled)

        if not self.ffmpeg_available:
            self._show_ffmpeg_warning()

        self._load_settings_from_config()
        self._apply_preset('enhanced')

    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("VK Track Modifier")
        self.setGeometry(100, 100, 1400, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self._init_left_panel(layout)
        self._init_right_panel(layout)

        self._init_bottom_panel(layout)
        self._init_progress_bar(layout)

    def _init_left_panel(self, parent_layout):
        """Инициализация левой панели со списком файлов"""
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_panel.setMinimumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_title = QLabel("Файлы")
        left_title.setStyleSheet(
            "font-size: 12px; font-weight: bold; "
            "padding: 6px; background: #2a2a2a; border-radius: 3px;"
        )
        left_layout.addWidget(left_title)

        # Кнопки управления списком
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

        # Список файлов
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

        # Статистика
        self.stats_label = QLabel("Файлов: 0 | Размер: 0 MB")
        self.stats_label.setStyleSheet(
            "padding: 6px; background-color: #2a2a2a; border-radius: 3px;"
        )
        left_layout.addWidget(self.stats_label)

        parent_layout.addWidget(left_panel)

    def _init_right_panel(self, parent_layout):
        """Инициализация правой панели с настройками"""
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

        parent_layout.addWidget(right_panel, 2)

    def _init_cover_section(self, layout):
        """Секция обложки"""
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
        """Секция метаданных"""
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
        """Секция пресетов"""
        presets_group = CollapsibleGroup("ПРОФИЛИ ОБРАБОТКИ")
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)

        self.btn_preset_enhanced = QPushButton("Расширенный")
        self.btn_preset_enhanced.clicked.connect(
            lambda: self._apply_preset('enhanced')
        )
        self.btn_preset_enhanced.setMinimumHeight(38)
        self.btn_preset_enhanced.setStyleSheet(self._get_button_style())

        self.btn_preset_reupload = QPushButton("Reupload")
        self.btn_preset_reupload.clicked.connect(
            lambda: self._apply_preset('reupload')
        )
        self.btn_preset_reupload.setMinimumHeight(38)
        self.btn_preset_reupload.setStyleSheet(self._get_button_style())

        presets_layout.addWidget(self.btn_preset_enhanced)
        presets_layout.addWidget(self.btn_preset_reupload)
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

    def _init_basic_params_section(self, layout):
        """Секция основных параметров"""
        basic_group = CollapsibleGroup("ОСНОВНЫЕ ПАРАМЕТРЫ")
        basic_layout = QGridLayout()
        basic_layout.setSpacing(6)

        self.method_pitch = QCheckBox("Изменить тональность")
        self.method_pitch.setChecked(True)
        basic_layout.addWidget(self.method_pitch, 0, 0)

        self.pitch_combo = QComboBox()
        self.pitch_combo.addItems([
            "-2 полутона", "-1 полутон", "+1 полутон", "+2 полутона",
            "Микро -0.5", "Микро +0.5"
        ])
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
        self.speed_combo.addItems([
            "0.97x", "0.98x", "0.99x", "1.01x", "1.02x", "1.03x",
            "0.995x", "1.005x"
        ])
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.setMinimumHeight(32)
        basic_layout.addWidget(self.speed_combo, 2, 1)

        self.method_eq = QCheckBox("Эквализация")
        self.method_eq.setChecked(True)
        basic_layout.addWidget(self.method_eq, 3, 0)

        self.eq_combo = QComboBox()
        self.eq_combo.addItems([
            "Слабая (-2dB)", "Средняя (-4dB)", "Сильная (-6dB)",
            "Средние частоты", "Высокие частоты"
        ])
        self.eq_combo.setCurrentIndex(1)
        self.eq_combo.setMinimumHeight(32)
        basic_layout.addWidget(self.eq_combo, 3, 1)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

    def _init_advanced_params_section(self, layout):
        """Секция дополнительных параметров"""
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
        self.method_broken_duration.setToolTip(
            "Создаёт конфликт длительности для сбоя парсинга"
        )
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
        """Секция технических настроек"""
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
        """Секция настроек качества"""
        quality_group = CollapsibleGroup("НАСТРОЙКИ КАЧЕСТВА")
        quality_layout = QGridLayout()
        quality_layout.setSpacing(6)

        quality_layout.addWidget(QLabel("Качество MP3:"), 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "320 kbps", "245 kbps (рекомендуется)", "175 kbps", "130 kbps"
        ])
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
        """Секция информации о треке"""
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
        """Нижняя панель с кнопками действий"""
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
        """Инициализация прогресс бара"""
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
        """Получает стиль для кнопок"""
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

    # Далее следуют методы обработки событий и логика работы
    # ... (продолжение в следующих сообщениях из-за ограничения длины)


    # ==================== МЕТОДЫ ОБРАБОТКИ СОБЫТИЙ ====================
    
    def _on_merge_toggled(self, checked):
        """Обработчик переключения режима сращивания"""
        self.btn_merge_track.setEnabled(checked)
        if not checked:
            self.extra_track_path = ""
            self.merge_track_label.setText("")

    def _select_merge_track(self):
        """Выбор трека для сращивания"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите трек для сращивания", "", "MP3 files (*.mp3)"
        )
        if file_path:
            self.extra_track_path = file_path
            self.merge_track_label.setText(f"Выбран: {os.path.basename(file_path)}")

    def _random_cover(self):
        """Генерация случайной обложки"""
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        pixmap = QPixmap(500, 500)
        pixmap.fill(QColor(
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        ))

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
        except Exception:
            pass

    def _random_metadata(self):
        """Генерация случайных метаданных"""
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
        """Предпросмотр эффектов (15 секунд)"""
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        settings = self._get_settings()
        track = self.tracks_info[self.current_track_index]

        temp_preview = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_preview.close()

        filters = FilterBuilder.build_filters(settings)

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
        """Удаление временного файла"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass

    def _show_ffmpeg_warning(self):
        """Показ предупреждения об отсутствии FFmpeg"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("FFmpeg не найден")
        msg.setText("Для работы программы требуется FFmpeg")
        msg.setInformativeText("Скачайте FFmpeg с ffmpeg.org и добавьте в PATH")
        msg.exec_()
        self.btn_start.setEnabled(False)

    def _load_settings_from_config(self):
        """Загрузка настроек из конфигурации"""
        self.output_dir = self.config_manager.get('output_dir', '')
        if self.output_dir:
            self.btn_output.setText(f"Папка: {os.path.basename(self.output_dir)}")
        self.chk_preserve_meta.setChecked(self.config_manager.get('preserve_metadata', True))
        self.chk_preserve_cover.setChecked(self.config_manager.get('preserve_cover', True))

    def _add_files(self):
        """Добавление файлов"""
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
                    track.set_hash(f.read())
                self.tracks_info.append(track)
                self.file_list.addItem(f"{os.path.basename(file_path)}\n{track.size_mb:.1f} MB")

        self._update_stats()
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.btn_remove.setEnabled(True)

    def _remove_current_file(self):
        """Удаление текущего файла"""
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
        """Очистка списка файлов"""
        self.input_files.clear()
        self.tracks_info.clear()
        self.file_list.clear()
        self._update_stats()
        self.btn_remove.setEnabled(False)
        self._clear_editor()

    def _clear_editor(self):
        """Очистка редактора"""
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()
        self.cover_preview.set_pixmap(None)
        self.cover_info.setText("Нет обложки")
        self.info_text.clear()

    def _on_file_selected(self, index):
        """Обработчик выбора файла"""
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

    def _load_metadata(self, track: TrackInfo):
        """Загрузка метаданных из файла"""
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

    def _extract_cover(self, track: TrackInfo):
        """Извлечение обложки из трека"""
        try:
            audio = MP3(track.file_path)
            if audio.tags:
                for tag in audio.tags.values():
                    if hasattr(tag, 'mime') and hasattr(tag, 'data'):
                        from mutagen.id3 import APIC
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
        """Выбор обложки"""
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
        """Удаление обложки"""
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            track.cover_data = None
            self._extract_cover(track)

    def _copy_meta_from_original(self):
        """Копирование метаданных из оригинала"""
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            self.edit_title.setText(track.title)
            self.edit_artist.setText(track.artist)
            self.edit_album.setText(track.album)
            self.edit_year.setText(track.year)
            self.edit_genre.setText(track.genre)

    def _clear_meta_fields(self):
        """Очистка полей метаданных"""
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()

    def _update_stats(self):
        """Обновление статистики"""
        count = len(self.input_files)
        total_size = sum(os.path.getsize(f) for f in self.input_files) / (1024 * 1024)
        self.stats_label.setText(f"Файлов: {count} | Размер: {total_size:.1f} MB")

    def _apply_preset(self, preset: str):
        """Применение пресета"""
        preset_data = PresetManager.get_preset(preset)
        if not preset_data:
            return

        # Применение настроек из пресета к UI элементам
        self.method_trim_silence.setChecked(preset_data.get('trim_silence', False))
        self.method_cut_fragment.setChecked(preset_data.get('cut_fragment', False))
        self.method_fade_out.setChecked(preset_data.get('fade_out', False))
        self.method_broken_duration.setChecked(preset_data.get('broken_duration', False))
        self.broken_type_combo.setCurrentIndex(preset_data.get('broken_type', 0))
        self.method_pitch.setChecked(preset_data.get('pitch', False))
        self.method_silence.setChecked(preset_data.get('silence', False))
        self.method_speed.setChecked(preset_data.get('speed', False))
        
        if preset_data.get('speed_value'):
            speed_values = get_speed_values()
            try:
                idx = speed_values.index(preset_data['speed_value'])
                self.speed_combo.setCurrentIndex(idx)
            except ValueError:
                pass
        
        self.method_eq.setChecked(preset_data.get('eq', False))
        self.method_phase.setChecked(preset_data.get('phase', False))
        self.method_noise.setChecked(preset_data.get('noise', False))
        self.method_compression.setChecked(preset_data.get('compression', False))
        self.method_ultrasound.setChecked(preset_data.get('ultrasound', False))
        self.method_dc_shift.setChecked(preset_data.get('dc_shift', False))
        self.method_merge.setChecked(preset_data.get('merge', False))
        self.method_bitrate_jitter.setChecked(preset_data.get('bitrate_jitter', False))
        self.method_frame_shift.setChecked(preset_data.get('frame_shift', False))
        self.method_fake_metadata.setChecked(preset_data.get('fake_metadata', False))
        self.method_reorder_tags.setChecked(preset_data.get('reorder_tags', False))
        self.chk_reupload.setChecked(preset_data.get('reupload', False))
        
        quality_map = get_quality_map()
        quality_value = preset_data.get('quality', '2')
        for k, v in quality_map.items():
            if v == quality_value:
                self.quality_combo.setCurrentIndex(k)
                break
        
        self.chk_rename.setChecked(preset_data.get('rename_files', True))
        self.chk_preserve_meta.setChecked(preset_data.get('preserve_metadata', True))
        self.chk_preserve_cover.setChecked(preset_data.get('preserve_cover', True))

    def _select_output_dir(self):
        """Выбор папки для сохранения"""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", 
            self.config_manager.get('output_dir', '')
        )
        if directory:
            self.output_dir = directory
            self.config_manager.set('output_dir', directory)
            self.btn_output.setText(f"Папка: {os.path.basename(directory)}")
            self.config_manager.save()

    def _get_settings(self) -> dict:
        """Получение текущих настроек"""
        quality_map = get_quality_map()
        pitch_values = get_pitch_values()
        speed_values = get_speed_values()
        eq_values = get_eq_values()
        phase_values = get_phase_values()
        noise_values = get_noise_values()

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

        # Сохранение в конфиг
        self.config_manager.set('pitch_value', settings['pitch_value'])
        self.config_manager.set('silence_duration', settings['silence_duration'])
        self.config_manager.set('speed_value', settings['speed_value'])
        self.config_manager.set('eq_value', settings['eq_value'])
        self.config_manager.set('quality', settings['quality'])
        self.config_manager.set('preserve_metadata', settings['preserve_metadata'])
        self.config_manager.set('preserve_cover', settings['preserve_cover'])
        self.config_manager.save()

        return settings

    def _start_modification(self):
        """Запуск обработки"""
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
        
        # Дополнительная проверка существования файла трека для сращивания
        if settings['methods']['merge'] and settings['extra_track_path']:
            if not os.path.exists(settings['extra_track_path']):
                QMessageBox.warning(self, "Внимание", 
                    f"Файл для сращивания не найден:\n{settings['extra_track_path']}")
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

    def _set_ui_enabled(self, enabled: bool):
        """Включение/выключение UI элементов"""
        self.btn_add.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled and self.file_list.count() > 0)
        self.btn_clear.setEnabled(enabled)
        self.btn_start.setEnabled(enabled)
        self.btn_output.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

    def _update_progress(self, current: int, total: int, file_name: str):
        """Обновление прогресса"""
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(
            f"Обработка {current}/{total}: {os.path.basename(file_name)}"
        )

    def _on_file_complete(self, file_name: str, success: bool, output_path: str):
        """Обработка завершения обработки файла"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if file_name in item.text():
                if success:
                    item.setText(f"[OK] {os.path.basename(file_name)}")
                else:
                    item.setText(f"[ERR] {os.path.basename(file_name)}")
                break

    def _on_all_complete(self, success_count: int, total_count: int):
        """Обработка завершения всех файлов"""
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
        except Exception:
            pass

    def _on_error(self, error_msg: str):
        """Обработка ошибки"""
        QMessageBox.critical(self, "Ошибка", error_msg)


def main():
    """Точка входа приложения"""
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
