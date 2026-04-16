"""Главное окно — компоновка и связка сигналов. v2.1 — все 15 фич."""

import os
import random
import tempfile
import logging
import time

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QShortcut, QTextEdit,
    QApplication, QSplitter, QInputDialog,
)
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QPixmap, QColor, QKeySequence, QDesktopServices

from .styles import (
    GLASS_BTN, ACCENT_BTN, ACCENT_BTN_SM, DANGER_BTN, PRESET_ACTIVE,
    get_stylesheet,
)
from .widgets import (
    GlassCard, CoverPreviewLabel, FileListWidget, GlassTabWidget, SliderWithLabel,
    QTextEditLogHandler, AudioPlayerWidget,
)
from .tabs.audio_tab import AudioTab
from .tabs.structure_tab import StructureTab
from .tabs.metadata_tab import MetadataTab
from .tabs.export_tab import ExportTab

from ..config import Config
from ..constants import APP_NAME, APP_VERSION, COVER_MAX_SIZE
from ..core.ffmpeg import find_ffmpeg, get_ffmpeg_version, run_ffmpeg, generate_spectrogram
from ..core.track_info import TrackInfo
from ..core.worker import ProcessingPool
from ..core.presets import (
    get_preset_settings, list_all_presets, BUILTIN_PRESETS,
    export_preset_to_file, import_preset_from_file,
)
from ..core.branding import BrandingEngine
from ..core.filters import FilterChain
from ..core.updater import UpdateChecker

logger = logging.getLogger('vk_modifier.main_window')


class MetadataLoader(QThread):
    """Фоновая загрузка метаданных файлов (не блокирует UI)."""
    track_loaded = pyqtSignal(int, object)  # index, TrackInfo
    all_loaded = pyqtSignal()

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        for i, fp in enumerate(self.file_paths):
            track = TrackInfo(fp)
            track.compute_hash()
            track.load_metadata()
            self.track_loaded.emit(i, track)
        self.all_loaded.emit()


class VKTrackModifier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.input_files: list[str] = []
        self.tracks_info: list[TrackInfo] = []
        self.output_dir = self.config.get('output_dir', '')
        self.current_track_index = -1
        self.pool = ProcessingPool(max_workers=self.config.get('max_workers', 2))
        self._active_preset = None
        self._paused = False
        self._processing_start_time = 0.0
        self._processing_timer = QTimer(self)
        self._processing_timer.setInterval(1000)
        self._processing_timer.timeout.connect(self._update_timer_display)
        self._current_theme = self.config.get('theme', 'dark')

        self._init_ui()
        self._connect_signals()
        self._apply_theme(self._current_theme)
        self._restore_state()
        self._setup_log_handler()
        self._check_for_updates()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI SETUP
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(80, 80, 1440, 920)
        self.setMinimumSize(1000, 650)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Левая панель: файлы
        self._build_left_panel(layout)

        # Правая панель: табы + управление
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setSpacing(10)
        right_lay.setContentsMargins(0, 0, 0, 0)

        self._build_presets_bar(right_lay)
        self._build_tabs(right_lay)
        self._build_bottom_bar(right_lay)
        self._build_progress(right_lay)

        # Лог-панель (Feature 6)
        self._build_log_panel(right_lay)

        layout.addWidget(right, 2)

        # Status bar
        self._build_status_bar()

        # Горячие клавиши
        self._setup_shortcuts()

    def _build_left_panel(self, parent):
        panel = QWidget()
        panel.setMinimumWidth(340)
        panel.setMaximumWidth(420)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        header = QLabel("Файлы")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: rgba(255,255,255,0.92); padding: 8px 4px;")
        lay.addWidget(header)

        hint = QLabel("Перетащите MP3 файлы или папки, или нажмите «Добавить»")
        hint.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.30); padding: 0 4px;")
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_add = QPushButton("Добавить")
        self.btn_add.setStyleSheet(ACCENT_BTN_SM)
        self.btn_add.setMinimumHeight(38)
        self.btn_add.clicked.connect(self._add_files)

        self.btn_remove = QPushButton("Удалить")
        self.btn_remove.setStyleSheet(GLASS_BTN)
        self.btn_remove.setMinimumHeight(38)
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._remove_selected)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.setStyleSheet(DANGER_BTN)
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.clicked.connect(self._clear_files)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addWidget(self.btn_clear)
        lay.addLayout(btn_row)

        self.file_list = FileListWidget()
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.file_list.files_dropped.connect(self._load_files)
        self.file_list.context_action.connect(self._on_context_action)
        self.file_list.order_changed.connect(self._on_file_order_changed)  # Feature 4
        lay.addWidget(self.file_list, 1)

        self.stats_label = QLabel("Файлов: 0  ·  0 MB")
        self.stats_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.35); padding: 6px 4px;")
        lay.addWidget(self.stats_label)

        # Инфо о треке
        info_card = GlassCard("Информация о треке")
        info_lay = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setPlaceholderText("Выберите файл из списка")
        info_lay.addWidget(self.info_text)
        info_card.setLayout(info_lay)
        lay.addWidget(info_card)

        # Аудиоплеер (Feature 7)
        self.player = AudioPlayerWidget()
        lay.addWidget(self.player)

        parent.addWidget(panel)

    def _build_presets_bar(self, parent):
        bar = QWidget()
        bar.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.025);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px;
            }
        """)
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(8)

        lbl = QLabel("Профиль:")
        lbl.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.40); border: none; background: transparent;")
        row.addWidget(lbl)

        self._preset_buttons = {}
        for name, data in BUILTIN_PRESETS.items():
            btn = QPushButton(data['label'])
            btn.setStyleSheet(ACCENT_BTN_SM)
            btn.setMinimumHeight(36)
            btn.setToolTip(data['description'])
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            row.addWidget(btn)
            self._preset_buttons[name] = btn

        row.addStretch()

        # Кнопки импорта/экспорта пресетов (Feature 1)
        self.btn_save_preset = QPushButton("Сохранить")
        self.btn_save_preset.setStyleSheet(GLASS_BTN)
        self.btn_save_preset.setMinimumHeight(36)
        self.btn_save_preset.setToolTip("Сохранить текущие настройки как пресет")
        self.btn_save_preset.clicked.connect(self._save_current_as_preset)
        row.addWidget(self.btn_save_preset)

        self.btn_import_preset = QPushButton("Импорт")
        self.btn_import_preset.setStyleSheet(GLASS_BTN)
        self.btn_import_preset.setMinimumHeight(36)
        self.btn_import_preset.setToolTip("Импорт пресета из JSON")
        self.btn_import_preset.clicked.connect(self._import_preset)
        row.addWidget(self.btn_import_preset)

        self.btn_export_preset = QPushButton("Экспорт")
        self.btn_export_preset.setStyleSheet(GLASS_BTN)
        self.btn_export_preset.setMinimumHeight(36)
        self.btn_export_preset.setToolTip("Экспорт текущих настроек в JSON")
        self.btn_export_preset.clicked.connect(self._export_preset)
        row.addWidget(self.btn_export_preset)

        parent.addWidget(bar)

    def _build_tabs(self, parent):
        self.tabs = GlassTabWidget()

        self.tab_audio = AudioTab()
        self.tab_structure = StructureTab()
        self.tab_metadata = MetadataTab()
        self.tab_export = ExportTab()

        self.TAB_AUDIO = self.tabs.add_tab(self.tab_audio, "Аудио")
        self.TAB_STRUCT = self.tabs.add_tab(self.tab_structure, "Структура")
        self.TAB_META = self.tabs.add_tab(self.tab_metadata, "Метаданные")
        self.TAB_EXPORT = self.tabs.add_tab(self.tab_export, "Экспорт")

        parent.addWidget(self.tabs, 1)

    def _build_bottom_bar(self, parent):
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 10, 0, 0)
        row.setSpacing(12)

        self.btn_output = QPushButton("Папка вывода")
        self.btn_output.setStyleSheet(GLASS_BTN)
        self.btn_output.setMinimumHeight(44)
        self.btn_output.clicked.connect(self._select_output_dir)

        self.btn_preview = QPushButton("Предпросмотр 15с")
        self.btn_preview.setStyleSheet(GLASS_BTN)
        self.btn_preview.setMinimumHeight(44)
        self.btn_preview.clicked.connect(self._preview_effects)

        # Пауза (Feature 3)
        self.btn_pause = QPushButton("Пауза")
        self.btn_pause.setStyleSheet(GLASS_BTN)
        self.btn_pause.setMinimumHeight(44)
        self.btn_pause.setVisible(False)
        self.btn_pause.clicked.connect(self._toggle_pause)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setStyleSheet(DANGER_BTN)
        self.btn_cancel.setMinimumHeight(44)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_processing)

        self.btn_start = QPushButton("ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setStyleSheet(ACCENT_BTN)
        self.btn_start.setMinimumHeight(50)
        self.btn_start.clicked.connect(self._start_processing)

        row.addWidget(self.btn_output)
        row.addWidget(self.btn_preview)
        row.addWidget(self.btn_pause)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_start, 2)
        parent.addWidget(bar)

    def _build_progress(self, parent):
        prog_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        prog_row.addWidget(self.progress_bar, 1)

        # Таймер обработки (Feature 5)
        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px; min-width: 60px;")
        self.timer_label.setVisible(False)
        prog_row.addWidget(self.timer_label)

        parent.addLayout(prog_row)

    def _build_log_panel(self, parent):
        """Feature 6: Live log panel."""
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setPlaceholderText("Лог обработки")
        self.log_text.setVisible(False)
        parent.addWidget(self.log_text)

    def _build_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        ffmpeg_ver = get_ffmpeg_version()
        self.status_ffmpeg = QLabel(f"FFmpeg: {ffmpeg_ver}")
        self.status_files = QLabel("0 файлов")
        self.status_version = QLabel(f"v{APP_VERSION}")
        self.status_bar.addWidget(self.status_ffmpeg)
        self.status_bar.addWidget(self.status_version)
        self.status_bar.addPermanentWidget(self.status_files)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self, self._add_files)
        QShortcut(QKeySequence("Delete"), self, self._remove_selected)
        QShortcut(QKeySequence("Ctrl+Return"), self, self._start_processing)
        QShortcut(QKeySequence("Ctrl+A"), self, lambda: self.file_list.selectAll())
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_settings_now)

    def _setup_log_handler(self):
        """Feature 6: Подключить логгер к панели."""
        handler = QTextEditLogHandler(self.log_text)
        handler.setLevel(logging.INFO)
        root_logger = logging.getLogger('vk_modifier')
        root_logger.addHandler(handler)

    # ══════════════════════════════════════════════════════════════════════════
    #  SIGNALS
    # ══════════════════════════════════════════════════════════════════════════

    def _connect_signals(self):
        # Worker
        self.pool.file_step.connect(self._on_file_step)
        self.pool.file_complete.connect(self._on_file_complete)
        self.pool.all_complete.connect(self._on_all_complete)

        # Badge updates
        self.tab_audio.settings_changed.connect(self._update_badges)
        self.tab_structure.settings_changed.connect(self._update_badges)
        self.tab_metadata.settings_changed.connect(self._update_badges)
        self.tab_export.settings_changed.connect(self._update_badges)

        # Per-track metadata/cover actions from metadata tab
        self.tab_metadata.request_copy_from_original.connect(self._copy_meta_from_original)
        self.tab_metadata.request_random_cover.connect(self._random_cover)
        self.tab_metadata.request_remove_cover.connect(self._remove_cover)

        # Feature 8: Batch apply metadata
        self.tab_metadata.request_batch_apply_metadata.connect(self._batch_apply_metadata)

    # ══════════════════════════════════════════════════════════════════════════
    #  FILE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def _add_files(self):
        last_dir = self.config.get('last_input_dir', '')
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите MP3 файлы", last_dir, "MP3 (*.mp3)"
        )
        if files:
            self.config.set('last_input_dir', os.path.dirname(files[0]))
            self._load_files(files)

    def _load_files(self, paths):
        new_paths = [p for p in paths if p not in self.input_files]
        if not new_paths:
            return

        start_idx = len(self.input_files)
        self.input_files.extend(new_paths)

        for fp in new_paths:
            name = os.path.basename(fp)
            self.file_list.addItem(f"{name}\n\u23f3 Загрузка...")
            self.tracks_info.append(None)

        self._loader = MetadataLoader(new_paths)
        self._loader_start_idx = start_idx
        self._loader.track_loaded.connect(self._on_track_loaded)
        self._loader.all_loaded.connect(self._on_all_tracks_loaded)
        self._loader.start()

        # Feature 9: Проверить профиль папки
        if new_paths:
            folder = os.path.dirname(new_paths[0])
            profile = self.config.get_folder_profile(folder)
            if profile:
                reply = QMessageBox.question(
                    self, "Профиль папки",
                    f"Для папки «{os.path.basename(folder)}» сохранён профиль настроек.\n"
                    "Применить?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self._apply_settings_dict(profile)

    def _on_track_loaded(self, rel_index, track):
        abs_index = self._loader_start_idx + rel_index
        if abs_index < len(self.tracks_info):
            self.tracks_info[abs_index] = track
            item = self.file_list.item(abs_index)
            if item:
                item.setText(track.summary)

    def _on_all_tracks_loaded(self):
        self._update_stats()
        self.btn_remove.setEnabled(self.file_list.count() > 0)
        if self.file_list.count() > 0 and not self.file_list.selectedItems():
            self.file_list.setCurrentRow(self.file_list.count() - 1)

    def _remove_selected(self):
        indices = self.file_list.get_selected_indices()
        if not indices:
            return
        for idx in reversed(indices):
            self.input_files.pop(idx)
            self.tracks_info.pop(idx)
            self.file_list.takeItem(idx)
        self._update_stats()
        self.btn_remove.setEnabled(self.file_list.count() > 0)
        self.current_track_index = -1
        if not self.file_list.selectedItems():
            self.info_text.clear()
            self.tab_metadata.cover_preview.set_pixmap(None)
            self.tab_metadata.cover_info.setText("Нет обложки")
            self.tab_metadata.btn_cover_remove.setEnabled(False)

    def _clear_files(self):
        self.input_files.clear()
        self.tracks_info.clear()
        self.file_list.clear()
        self._update_stats()
        self.btn_remove.setEnabled(False)
        self.current_track_index = -1
        self.info_text.clear()
        self.tab_metadata.cover_preview.set_pixmap(None)
        self.tab_metadata.cover_info.setText("Нет обложки")
        self.tab_metadata.btn_cover_remove.setEnabled(False)

    def _on_selection_changed(self):
        indices = self.file_list.get_selected_indices()
        if len(indices) == 1:
            idx = indices[0]
            self.current_track_index = idx
            track = self.tracks_info[idx] if idx < len(self.tracks_info) else None
            if track:
                self.info_text.setText(track.detail_info)
                self._show_track_cover(track)
                # Feature 7: загрузить в плеер
                self.player.load_file(track.file_path)
                # Feature 11: загрузить волну
                self.tab_structure.load_track_waveform(track.file_path)
                self.tab_structure.set_track_duration(track.duration_sec)
        elif len(indices) > 1:
            self.info_text.setText(f"Выбрано файлов: {len(indices)}")
            self.current_track_index = -1
        else:
            self.current_track_index = -1
        self.btn_remove.setEnabled(len(indices) > 0)

    def _show_track_cover(self, track):
        if track.cover_data:
            px = QPixmap()
            px.loadFromData(track.cover_data)
            self.tab_metadata.cover_preview.set_pixmap(px)
            self.tab_metadata.cover_info.setText("Оригинальная обложка")
            self.tab_metadata.btn_cover_remove.setEnabled(True)
        else:
            self.tab_metadata.cover_preview.set_pixmap(None)
            self.tab_metadata.cover_info.setText("Нет обложки")
            self.tab_metadata.btn_cover_remove.setEnabled(False)

    def _on_context_action(self, action, indices):
        if action == 'select_all':
            self.file_list.selectAll()
        elif action == 'remove':
            for idx in reversed(indices):
                self.input_files.pop(idx)
                self.tracks_info.pop(idx)
                self.file_list.takeItem(idx)
            self._update_stats()
        elif action == 'open_folder' and len(indices) == 1:
            fp = self.input_files[indices[0]]
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(fp)))
        elif action == 'play' and len(indices) == 1:
            fp = self.input_files[indices[0]]
            # Feature 7: воспроизвести во встроенном плеере
            self.player.load_file(fp)
        elif action == 'cover' and len(indices) >= 1:
            path, _ = QFileDialog.getOpenFileName(
                self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg *.webp)"
            )
            if path:
                with open(path, 'rb') as f:
                    cover_data = f.read()
                ext = os.path.splitext(path)[1].lower()
                mime = 'image/png' if ext == '.png' else 'image/jpeg'
                for idx in indices:
                    if idx < len(self.tracks_info) and self.tracks_info[idx]:
                        self.tracks_info[idx].custom_cover_data = cover_data
                        self.tracks_info[idx].custom_cover_mime = mime
                if len(indices) == 1:
                    px = QPixmap(path)
                    self.tab_metadata.cover_preview.set_pixmap(px)
                    self.tab_metadata.cover_info.setText(os.path.basename(path))
                    self.tab_metadata.btn_cover_remove.setEnabled(True)
        elif action == 'meta' and len(indices) == 1:
            idx = indices[0]
            if idx < len(self.tracks_info) and self.tracks_info[idx]:
                self.tab_metadata.fill_from_track(self.tracks_info[idx])
                self.tabs.tab_bar.setCurrentIndex(self.TAB_META)

    # Feature 4: Drag-drop reorder sync
    def _on_file_order_changed(self):
        """Синхронизировать внутренние списки с новым порядком в UI."""
        new_files = []
        new_tracks = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            text = item.text() if item else ''
            # Найти соответствующий трек по тексту
            found = False
            for j, track in enumerate(self.tracks_info):
                if track and track.summary == text and self.input_files[j] not in new_files:
                    new_files.append(self.input_files[j])
                    new_tracks.append(track)
                    found = True
                    break
            if not found:
                # Fallback: оставить по индексу
                if i < len(self.input_files):
                    new_files.append(self.input_files[i])
                    new_tracks.append(self.tracks_info[i])

        if len(new_files) == len(self.input_files):
            self.input_files = new_files
            self.tracks_info = new_tracks

    def _update_stats(self):
        n = len(self.input_files)
        total = sum(os.path.getsize(f) for f in self.input_files if os.path.exists(f)) / (1024 * 1024) if n else 0
        self.stats_label.setText(f"Файлов: {n}  ·  {total:.1f} MB")
        self.status_files.setText(f"{n} файлов")

    # ══════════════════════════════════════════════════════════════════════════
    #  PER-TRACK COVER/METADATA
    # ══════════════════════════════════════════════════════════════════════════

    def _copy_meta_from_original(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return
        track = self.tracks_info[self.current_track_index]
        if track:
            self.tab_metadata.fill_from_track(track)

    def _random_cover(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return
        track = self.tracks_info[self.current_track_index]
        if not track:
            return

        pixmap = QPixmap(500, 500)
        pixmap.fill(QColor(random.randint(40, 200), random.randint(40, 200), random.randint(40, 200)))
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        pixmap.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            track.custom_cover_data = f.read()
        track.custom_cover_mime = 'image/png'
        self.tab_metadata.cover_preview.set_pixmap(pixmap)
        self.tab_metadata.cover_info.setText("Случайная обложка")
        self.tab_metadata.btn_cover_remove.setEnabled(True)
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    def _remove_cover(self):
        if self.current_track_index < 0:
            return
        track = self.tracks_info[self.current_track_index]
        if track:
            track.cover_data = None
            track.custom_cover_data = None
        self.tab_metadata.cover_preview.set_pixmap(None)
        self.tab_metadata.cover_info.setText("Нет обложки")
        self.tab_metadata.btn_cover_remove.setEnabled(False)

    # Feature 8: Batch apply metadata
    def _batch_apply_metadata(self, meta_dict):
        """Применить метаданные ко всем выделенным трекам."""
        indices = self.file_list.get_selected_indices()
        if not indices:
            QMessageBox.warning(self, "Внимание", "Выделите треки в списке")
            return
        applied = 0
        for idx in indices:
            if idx < len(self.tracks_info) and self.tracks_info[idx]:
                track = self.tracks_info[idx]
                if meta_dict.get('title'):
                    track.custom_title = meta_dict['title']
                if meta_dict.get('artist'):
                    track.custom_artist = meta_dict['artist']
                if meta_dict.get('album'):
                    track.custom_album = meta_dict['album']
                applied += 1
        logger.info(f"Метаданные применены к {applied} трекам")

    # ══════════════════════════════════════════════════════════════════════════
    #  PREVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def _preview_effects(self):
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        track = self.tracks_info[self.current_track_index]
        if not track:
            return

        settings = self._get_all_settings()
        chain = FilterChain(settings, track.duration_sec)
        _, filter_str, map_label = chain.build()

        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp.close()

        cmd = ['-i', track.file_path, '-t', '15']
        if map_label:
            cmd.extend(['-filter_complex', filter_str, '-map', map_label])
        elif filter_str:
            cmd.extend(['-af', filter_str])
        cmd.extend(['-codec:a', 'libmp3lame', '-q:a', '2', '-y', tmp.name])

        try:
            result = run_ffmpeg(cmd, timeout=30)
            if result.returncode == 0:
                # Feature 7: открыть во встроенном плеере вместо системного
                self.player.load_file(tmp.name)
                self.player.set_processed(tmp.name)
                QTimer.singleShot(120000, lambda: self._delete_temp(tmp.name))
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    f"Ошибка предпросмотра:\n{result.stderr[:500]}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    @staticmethod
    def _delete_temp(path):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  PRESETS (Feature 1)
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_preset(self, name):
        settings = get_preset_settings(name)
        if not settings:
            return

        self.tab_audio.reset_to_defaults()
        self.tab_structure.reset_to_defaults()
        self.tab_metadata.reset_to_defaults()
        self.tab_export.reset_to_defaults()

        self.tab_audio.apply_settings(settings)
        self.tab_structure.apply_settings(settings)
        self.tab_metadata.apply_settings(settings)
        self.tab_export.apply_settings(settings)

        for n, btn in self._preset_buttons.items():
            btn.setStyleSheet(PRESET_ACTIVE if n == name else ACCENT_BTN_SM)
        self._active_preset = name

        self._update_badges()

    def _save_current_as_preset(self):
        """Feature 1: Сохранить текущие настройки как пользовательский пресет."""
        name, ok = QInputDialog.getText(self, "Сохранить пресет", "Название пресета:")
        if not ok or not name.strip():
            return
        name = name.strip()
        settings = self._get_all_settings()
        # Убрать runtime-only поля
        settings.pop('user_metadata', None)
        settings.pop('merge_track_path', None)
        settings.pop('cover_path', None)
        self.config.save_preset(name, settings)
        logger.info(f"Пресет '{name}' сохранён")
        QMessageBox.information(self, "Готово", f"Пресет «{name}» сохранён")

    def _import_preset(self):
        """Feature 1: Импорт пресета из JSON."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт пресета", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            name, settings = import_preset_from_file(path)
            self.config.save_preset(name, settings)
            self._apply_settings_dict(settings)
            QMessageBox.information(self, "Готово", f"Пресет «{name}» импортирован")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка импорта:\n{e}")

    def _export_preset(self):
        """Feature 1: Экспорт текущих настроек в JSON."""
        name = self._active_preset or 'custom'
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт пресета", f"{name}.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            settings = self._get_all_settings()
            settings.pop('user_metadata', None)
            export_preset_to_file(name, settings, path)
            QMessageBox.information(self, "Готово", f"Пресет экспортирован в {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{e}")

    # ══════════════════════════════════════════════════════════════════════════
    #  BADGES
    # ══════════════════════════════════════════════════════════════════════════

    def _update_badges(self):
        self.tabs.set_badge(self.TAB_AUDIO, self.tab_audio.active_count())
        self.tabs.set_badge(self.TAB_STRUCT, self.tab_structure.active_count())
        self.tabs.set_badge(self.TAB_META, self.tab_metadata.active_count())
        self.tabs.set_badge(self.TAB_EXPORT, self.tab_export.active_count())

    # ══════════════════════════════════════════════════════════════════════════
    #  PROCESSING
    # ══════════════════════════════════════════════════════════════════════════

    def _get_all_settings(self) -> dict:
        s = {}
        s.update(self.tab_audio.get_settings())
        s.update(self.tab_structure.get_settings())
        s.update(self.tab_metadata.get_settings())
        s.update(self.tab_export.get_settings())
        s['user_metadata'] = self.tab_metadata.get_metadata_dict()
        return s

    def _apply_settings_dict(self, s: dict):
        """Применить словарь настроек ко всем табам."""
        self.tab_audio.apply_settings(s)
        self.tab_structure.apply_settings(s)
        self.tab_metadata.apply_settings(s)
        self.tab_export.apply_settings(s)
        self._update_badges()

    def _select_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка вывода", self.output_dir)
        if d:
            self.output_dir = d
            self.config.set('output_dir', d)
            self.config.save()
            self.btn_output.setText(f"Папка: {os.path.basename(d)}")

    def _start_processing(self):
        if not self.input_files:
            QMessageBox.warning(self, "Внимание", "Добавьте файлы для обработки!")
            return

        if any(t is None for t in self.tracks_info):
            QMessageBox.warning(self, "Внимание", "Подождите, метаданные ещё загружаются...")
            return

        if not self.output_dir:
            reply = QMessageBox.question(
                self, "Папка не выбрана",
                "Использовать папку исходных файлов?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.output_dir = os.path.dirname(self.input_files[0])
            else:
                return

        settings = self._get_all_settings()

        if settings.get('merge_enabled') and not settings.get('merge_track_path'):
            QMessageBox.warning(self, "Внимание", "Включено сращивание, но трек не выбран!")
            return

        if settings.get('frame_shift') and settings.get('broken_duration_enabled'):
            QMessageBox.warning(
                self, "Конфликт",
                "«Сдвиг фреймов» и «Модификация длительности» конфликтуют.\n"
                "Сдвиг фреймов будет отключён."
            )
            settings['frame_shift'] = False

        os.makedirs(self.output_dir, exist_ok=True)

        # UI
        self._set_processing_ui(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.input_files))
        self.progress_bar.setValue(0)

        # Feature 6: показать лог-панель
        self.log_text.setVisible(True)
        self.log_text.clear()

        # Feature 5: таймер
        self._processing_start_time = time.time()
        self.timer_label.setVisible(True)
        self._processing_timer.start()

        # Feature 9: сохранить профиль папки
        if self.input_files:
            folder = os.path.dirname(self.input_files[0])
            self.config.save_folder_profile(folder, settings)

        # Обновить max_workers
        self.pool.pool.setMaxThreadCount(settings.get('max_workers', 2))

        # Запуск
        self.pool.start(self.input_files, self.tracks_info, self.output_dir, settings)

    def _cancel_processing(self):
        self.pool.cancel()
        self._set_processing_ui(False)
        self.progress_bar.setVisible(False)
        self._processing_timer.stop()
        self.timer_label.setVisible(False)
        self._paused = False

    # Feature 3: Пауза
    def _toggle_pause(self):
        if self._paused:
            self.pool.resume()
            self._paused = False
            self.btn_pause.setText("Пауза")
            self.btn_pause.setStyleSheet(GLASS_BTN)
        else:
            self.pool.pause()
            self._paused = True
            self.btn_pause.setText("Продолжить")
            self.btn_pause.setStyleSheet(ACCENT_BTN_SM)

    def _set_processing_ui(self, processing: bool):
        for w in [self.btn_add, self.btn_clear, self.btn_start, self.btn_output, self.btn_preview]:
            w.setEnabled(not processing)
        self.btn_cancel.setVisible(processing)
        self.btn_pause.setVisible(processing)
        self.btn_remove.setEnabled(not processing and self.file_list.count() > 0)

    # Feature 5: Таймер
    def _update_timer_display(self):
        elapsed = int(time.time() - self._processing_start_time)
        m, s = divmod(elapsed, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def _on_file_step(self, file_path, step, total, name):
        self.progress_bar.setFormat(f"{os.path.basename(file_path)}: {name} ({step}/{total})")

    def _on_file_complete(self, file_path, success, output, error):
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item and os.path.basename(file_path) in item.text():
                prefix = "\u2713 " if success else "\u2717 "
                item.setText(prefix + os.path.basename(file_path))
                break

        # Feature 7: Установить обработанный файл для A/B
        if success and output and self.current_track_index >= 0:
            cur_fp = self.input_files[self.current_track_index]
            if cur_fp == file_path:
                self.player.set_processed(output)

    def _on_all_complete(self, ok, total):
        self.progress_bar.setVisible(False)
        self._set_processing_ui(False)
        self._processing_timer.stop()
        self._paused = False

        # Feature 5: показать итоговое время
        elapsed = int(time.time() - self._processing_start_time)
        m, s = divmod(elapsed, 60)
        time_str = f"{m:02d}:{s:02d}"
        self.timer_label.setText(f"Готово за {time_str}")

        if ok == total:
            QMessageBox.information(
                self, "Готово",
                f"Все {total} треков обработаны за {time_str}!\n"
                f"Сохранено в: {self.output_dir}"
            )
        else:
            QMessageBox.warning(
                self, "Завершено",
                f"Успешно: {ok} из {total}\nОшибок: {total - ok}\nВремя: {time_str}"
            )

        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))

    # ══════════════════════════════════════════════════════════════════════════
    #  SETTINGS PERSISTENCE (Feature 2)
    # ══════════════════════════════════════════════════════════════════════════

    def _save_settings_now(self):
        """Сохранить все текущие настройки в конфиг."""
        settings = self._get_all_settings()
        settings.pop('user_metadata', None)
        settings.pop('merge_track_path', None)
        for key, val in settings.items():
            self.config.set(key, val)
        self.config.save()
        logger.info("Настройки сохранены")

    def _restore_settings_from_config(self):
        """Feature 2: Восстановить настройки из конфига."""
        data = self.config.get_all()
        self.tab_audio.apply_settings(data)
        self.tab_structure.apply_settings(data)
        self.tab_metadata.apply_settings(data)
        self.tab_export.apply_settings(data)
        self._update_badges()

    # ══════════════════════════════════════════════════════════════════════════
    #  AUTO-UPDATE (Feature 15)
    # ══════════════════════════════════════════════════════════════════════════

    def _check_for_updates(self):
        self._updater = UpdateChecker()
        self._updater.update_available.connect(self._on_update_available)
        self._updater.start()

    def _on_update_available(self, version, url):
        self.status_version.setText(f"v{APP_VERSION} (обновление {version})")
        self.status_version.setStyleSheet(
            "color: rgba(90,200,250,0.90); font-size: 11px; padding: 2px 8px; "
            "cursor: pointer; text-decoration: underline;"
        )
        self._update_url = url
        self.status_version.mousePressEvent = lambda e: QDesktopServices.openUrl(QUrl(url))

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE
    # ══════════════════════════════════════════════════════════════════════════

    def _restore_state(self):
        # Геометрия
        geom = self.config.get('window_geometry')
        if geom and isinstance(geom, list) and len(geom) == 4:
            self.setGeometry(*geom)

        if self.output_dir:
            self.btn_output.setText(f"Папка: {os.path.basename(self.output_dir)}")

        if not find_ffmpeg():
            QMessageBox.warning(
                self, "FFmpeg не найден",
                "Для работы требуется FFmpeg.\n"
                "Скачайте с ffmpeg.org или поместите ffmpeg.exe рядом с программой."
            )
            self.btn_start.setEnabled(False)
            self.btn_preview.setEnabled(False)

        # Feature 2: Восстановить настройки
        self._restore_settings_from_config()

        # Применить последний пресет (перезапишет восстановленные настройки)
        last = self.config.get('last_preset', 'enhanced')
        if last:
            self._apply_preset(last)

    def closeEvent(self, event):
        # Feature 2: Сохранить ВСЕ настройки
        self._save_settings_now()

        if self._active_preset:
            self.config.set('last_preset', self._active_preset)

        # Геометрия
        g = self.geometry()
        self.config.set('window_geometry', [g.x(), g.y(), g.width(), g.height()])

        self.config.save()

        # Остановить плеер
        if hasattr(self.player, '_player') and self.player._player:
            self.player._stop()

        super().closeEvent(event)
