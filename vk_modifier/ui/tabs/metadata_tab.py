"""Таб «Брендирование» — шаблоны имён, метаданных, обложки + per-track редактирование."""

import os
import random
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QFrame,
    QCheckBox, QLabel, QPushButton, QLineEdit, QComboBox,
    QHBoxLayout, QRadioButton, QButtonGroup, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from ..widgets import GlassCard, CoverPreviewLabel
from ..styles import GLASS_BTN
from ...constants import TEMPLATE_VARS_HELP


class MetadataTab(QScrollArea):
    settings_changed = pyqtSignal()
    # Сигнал для запросов, требующих данные из main_window (текущий трек)
    request_copy_from_original = pyqtSignal()
    request_random_cover = pyqtSignal()
    request_remove_cover = pyqtSignal()
    request_batch_apply_metadata = pyqtSignal(dict)  # metadata dict

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cover_path = ''

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(content)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 8, 6, 0)

        # ── Шаблон имени файла ──
        card1 = GlassCard("Шаблон имени файла")
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)

        lbl = QLabel("Шаблон:")
        lbl.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid.addWidget(lbl, 0, 0)
        self.edit_filename_tpl = QLineEdit()
        self.edit_filename_tpl.setPlaceholderText("{prefix}_{counter:03d}_{original_name}")
        self.edit_filename_tpl.setText("{prefix}_{counter:03d}_{original_name}")
        self.edit_filename_tpl.textChanged.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.edit_filename_tpl, 0, 1)

        lbl2 = QLabel("Prefix:")
        lbl2.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid.addWidget(lbl2, 1, 0)
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setPlaceholderText("VK")
        self.edit_prefix.textChanged.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.edit_prefix, 1, 1)

        lbl3 = QLabel("Tag:")
        lbl3.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid.addWidget(lbl3, 2, 0)
        self.edit_tag = QLineEdit()
        self.edit_tag.setPlaceholderText("REUPLOAD, REMIX, EDIT...")
        self.edit_tag.textChanged.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.edit_tag, 2, 1)

        # Подсказка по переменным
        hint = QLabel("Переменные: {original_name}, {title}, {artist}, {counter:03d}, {tag}, {prefix}, {md5_short}, {date}, {random}")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 10px;")
        grid.addWidget(hint, 3, 0, 1, 2)

        card1.setLayout(grid)
        lay.addWidget(card1)

        # ── Теги ID3 (per-track редактирование, как в v1) ──
        card_tags = GlassCard("Теги ID3")
        grid_tags = QGridLayout()
        grid_tags.setSpacing(8)
        grid_tags.setColumnStretch(1, 1)

        labels = ["Название:", "Исполнитель:", "Альбом:", "Год:", "Жанр:"]
        placeholders = ["Оставить оригинал", "Оставить оригинал", "Оставить оригинал", "2024", "Pop, Rock..."]
        names = ['title', 'artist', 'album', 'year', 'genre']
        self.meta_edits = {}
        for i, (label, ph, name) in enumerate(zip(labels, placeholders, names)):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
            edit = QLineEdit()
            edit.setPlaceholderText(ph)
            edit.textChanged.connect(lambda: self.settings_changed.emit())
            grid_tags.addWidget(lbl, i, 0)
            grid_tags.addWidget(edit, i, 1)
            self.meta_edits[name] = edit

        # Удобный доступ
        self.edit_title = self.meta_edits['title']
        self.edit_artist = self.meta_edits['artist']
        self.edit_album = self.meta_edits['album']
        self.edit_year = self.meta_edits['year']
        self.edit_genre = self.meta_edits['genre']

        # Кнопки управления тегами
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_meta_clear = QPushButton("Очистить")
        self.btn_meta_clear.setStyleSheet(GLASS_BTN)
        self.btn_meta_clear.setMinimumHeight(36)
        self.btn_meta_clear.clicked.connect(self._clear_meta_fields)

        self.btn_meta_copy = QPushButton("Из оригинала")
        self.btn_meta_copy.setStyleSheet(GLASS_BTN)
        self.btn_meta_copy.setMinimumHeight(36)
        self.btn_meta_copy.clicked.connect(lambda: self.request_copy_from_original.emit())

        self.btn_meta_random = QPushButton("Случайные")
        self.btn_meta_random.setStyleSheet(GLASS_BTN)
        self.btn_meta_random.setMinimumHeight(36)
        self.btn_meta_random.clicked.connect(self._random_metadata)

        btn_row.addWidget(self.btn_meta_clear)
        btn_row.addWidget(self.btn_meta_copy)
        btn_row.addWidget(self.btn_meta_random)
        grid_tags.addLayout(btn_row, len(labels), 0, 1, 2)

        # Чекбокс REUPLOAD (как в v1)
        self.chk_reupload = QCheckBox("Добавить (REUPLOAD) к названию")
        self.chk_reupload.toggled.connect(lambda: self.settings_changed.emit())
        grid_tags.addWidget(self.chk_reupload, len(labels) + 1, 0, 1, 2)

        # Кнопка «Применить ко всем выделенным»
        self.btn_batch_apply = QPushButton("Применить ко всем выделенным")
        self.btn_batch_apply.setStyleSheet(GLASS_BTN)
        self.btn_batch_apply.setMinimumHeight(36)
        self.btn_batch_apply.setToolTip("Применить введённые теги ко всем выделенным трекам")
        self.btn_batch_apply.clicked.connect(
            lambda: self.request_batch_apply_metadata.emit(self.get_metadata_dict())
        )
        grid_tags.addWidget(self.btn_batch_apply, len(labels) + 2, 0, 1, 2)

        card_tags.setLayout(grid_tags)
        lay.addWidget(card_tags)

        # ── Шаблон метаданных (title template) ──
        card2 = GlassCard("Шаблоны метаданных")
        grid2 = QGridLayout()
        grid2.setSpacing(8)
        grid2.setColumnStretch(1, 1)

        lbl_t = QLabel("Title шаблон:")
        lbl_t.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid2.addWidget(lbl_t, 0, 0)
        self.edit_title_tpl = QLineEdit()
        self.edit_title_tpl.setPlaceholderText("{original_title} ({tag})")
        self.edit_title_tpl.setText("{original_title}")
        self.edit_title_tpl.textChanged.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.edit_title_tpl, 0, 1)

        # Манипуляции тегами
        self.chk_fake_meta = QCheckBox("Фальшивые метаданные (случайный comment)")
        self.chk_fake_meta.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_fake_meta, 1, 0, 1, 2)

        self.chk_reorder = QCheckBox("Переупорядочить ID3 теги")
        self.chk_reorder.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_reorder, 2, 0, 1, 2)

        self.chk_preserve = QCheckBox("Сохранить оригинальные метаданные")
        self.chk_preserve.setChecked(True)
        self.chk_preserve.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_preserve, 3, 0, 1, 2)

        card2.setLayout(grid2)
        lay.addWidget(card2)

        # ── Обложка ──
        card3 = GlassCard("Обложка")
        cover_lay = QVBoxLayout()
        cover_lay.setSpacing(12)

        # Режим обложки
        mode_row = QHBoxLayout()
        self.cover_group = QButtonGroup(self)
        modes = [
            ('original', 'Оригинальная'),
            ('single', 'Одна на все'),
            ('remove', 'Удалить'),
            ('random', 'Случайная'),
        ]
        for val, label in modes:
            rb = QRadioButton(label)
            rb.setProperty('mode_value', val)
            rb.toggled.connect(lambda: self.settings_changed.emit())
            self.cover_group.addButton(rb)
            mode_row.addWidget(rb)
            if val == 'original':
                rb.setChecked(True)
        cover_lay.addLayout(mode_row)

        # Превью + кнопки управления обложкой
        preview_row = QHBoxLayout()
        self.cover_preview = CoverPreviewLabel()
        self.cover_preview.clicked.connect(self._select_cover)
        preview_row.addWidget(self.cover_preview)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)

        self.btn_cover_select = QPushButton("Выбрать обложку")
        self.btn_cover_select.setStyleSheet(GLASS_BTN)
        self.btn_cover_select.setMinimumHeight(38)
        self.btn_cover_select.clicked.connect(self._select_cover)
        btn_col.addWidget(self.btn_cover_select)

        self.btn_cover_remove = QPushButton("Удалить")
        self.btn_cover_remove.setStyleSheet(GLASS_BTN)
        self.btn_cover_remove.setMinimumHeight(38)
        self.btn_cover_remove.setEnabled(False)
        self.btn_cover_remove.clicked.connect(lambda: self.request_remove_cover.emit())
        btn_col.addWidget(self.btn_cover_remove)

        self.btn_cover_random = QPushButton("Случайная")
        self.btn_cover_random.setStyleSheet(GLASS_BTN)
        self.btn_cover_random.setMinimumHeight(38)
        self.btn_cover_random.clicked.connect(lambda: self.request_random_cover.emit())
        btn_col.addWidget(self.btn_cover_random)

        self.cover_info = QLabel("Нет обложки")
        self.cover_info.setWordWrap(True)
        self.cover_info.setAlignment(Qt.AlignCenter)
        self.cover_info.setStyleSheet("color: rgba(255,255,255,0.30); font-size: 12px;")
        btn_col.addWidget(self.cover_info)

        btn_col.addStretch()
        preview_row.addLayout(btn_col)
        cover_lay.addLayout(preview_row)

        card3.setLayout(cover_lay)
        lay.addWidget(card3)

        lay.addStretch()
        self.setWidget(content)

    def _select_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._cover_path = path
            self.cover_preview.set_pixmap(QPixmap(path))
            self.cover_info.setText(os.path.basename(path))
            self.btn_cover_remove.setEnabled(True)
            # Переключить на режим "одна на все"
            for btn in self.cover_group.buttons():
                if btn.property('mode_value') == 'single':
                    btn.setChecked(True)
                    break

    def _clear_meta_fields(self):
        """Очистить все поля тегов."""
        for edit in self.meta_edits.values():
            edit.clear()

    def _random_metadata(self):
        """Заполнить случайными метаданными (как в v1)."""
        titles = ["Track", "Song", "Melody", "Rhythm", "Harmony", "Beat", "Flow", "Vibe", "Sound", "Wave"]
        artists = ["Artist", "Musician", "Producer", "DJ", "Band", "Project", "Studio", "Creator"]
        albums = ["Album", "Collection", "Mix", "Set", "Compilation", "Series", "Volume"]
        genres = ["Pop", "Rock", "Electronic", "Hip Hop", "Jazz", "Classical", "Ambient", "Dance"]
        self.edit_title.setText(f"{random.choice(titles)} {random.randint(1, 999)}")
        self.edit_artist.setText(f"{random.choice(artists)} {random.randint(1, 99)}")
        self.edit_album.setText(f"{random.choice(albums)} {random.randint(2020, 2026)}")
        self.edit_year.setText(str(random.randint(2000, 2026)))
        self.edit_genre.setText(random.choice(genres))

    def fill_from_track(self, track_info):
        """Заполнить поля из оригинальных тегов трека."""
        self.edit_title.setText(track_info.title or '')
        self.edit_artist.setText(track_info.artist or '')
        self.edit_album.setText(track_info.album or '')
        self.edit_year.setText(track_info.year or '')
        self.edit_genre.setText(track_info.genre or '')

    def _get_cover_mode(self) -> str:
        btn = self.cover_group.checkedButton()
        return btn.property('mode_value') if btn else 'original'

    def get_metadata_dict(self) -> dict:
        """Вернуть введённые значения тегов (для передачи в worker)."""
        return {k: e.text() for k, e in self.meta_edits.items()}

    def active_count(self) -> int:
        count = 0
        if self.edit_tag.text(): count += 1
        if self.edit_prefix.text(): count += 1
        if self.chk_fake_meta.isChecked(): count += 1
        if self.chk_reorder.isChecked(): count += 1
        if self.chk_reupload.isChecked(): count += 1
        if self._get_cover_mode() != 'original': count += 1
        # Считаем заполненные поля тегов
        for name in ('title', 'artist', 'album', 'year', 'genre'):
            if self.meta_edits[name].text():
                count += 1
        return count

    def get_settings(self) -> dict:
        return {
            'filename_template': self.edit_filename_tpl.text(),
            'title_template': self.edit_title_tpl.text(),
            'brand_prefix': self.edit_prefix.text(),
            'brand_tag': self.edit_tag.text(),
            'brand_artist': self.edit_artist.text(),
            'brand_album': self.edit_album.text(),
            'brand_year': self.edit_year.text(),
            'brand_genre': self.edit_genre.text(),
            'brand_title': self.edit_title.text(),
            'reupload': self.chk_reupload.isChecked(),
            'fake_metadata': self.chk_fake_meta.isChecked(),
            'reorder_tags': self.chk_reorder.isChecked(),
            'preserve_metadata': self.chk_preserve.isChecked(),
            'cover_mode': self._get_cover_mode(),
            'cover_path': self._cover_path,
        }

    def apply_settings(self, s: dict):
        if 'filename_template' in s: self.edit_filename_tpl.setText(s['filename_template'])
        if 'title_template' in s: self.edit_title_tpl.setText(s['title_template'])
        if 'brand_prefix' in s: self.edit_prefix.setText(s['brand_prefix'])
        if 'brand_tag' in s: self.edit_tag.setText(s['brand_tag'])
        if 'brand_artist' in s: self.edit_artist.setText(s['brand_artist'])
        if 'brand_album' in s: self.edit_album.setText(s['brand_album'])
        if 'brand_year' in s: self.edit_year.setText(s['brand_year'])
        if 'brand_genre' in s: self.edit_genre.setText(s['brand_genre'])
        if 'brand_title' in s: self.edit_title.setText(s['brand_title'])
        if 'reupload' in s: self.chk_reupload.setChecked(s['reupload'])
        if 'fake_metadata' in s: self.chk_fake_meta.setChecked(s['fake_metadata'])
        if 'reorder_tags' in s: self.chk_reorder.setChecked(s['reorder_tags'])
        if 'preserve_metadata' in s: self.chk_preserve.setChecked(s['preserve_metadata'])
        if 'cover_mode' in s:
            for btn in self.cover_group.buttons():
                if btn.property('mode_value') == s['cover_mode']:
                    btn.setChecked(True)

    def reset_to_defaults(self):
        self.edit_filename_tpl.setText("{prefix}_{counter:03d}_{original_name}")
        self.edit_title_tpl.setText("{original_title}")
        self.edit_prefix.clear()
        self.edit_tag.clear()
        # Очистить все поля тегов
        for edit in self.meta_edits.values():
            edit.clear()
        self.chk_reupload.setChecked(False)
        self.chk_fake_meta.setChecked(False)
        self.chk_reorder.setChecked(False)
        self.chk_preserve.setChecked(True)
        for btn in self.cover_group.buttons():
            if btn.property('mode_value') == 'original':
                btn.setChecked(True)
