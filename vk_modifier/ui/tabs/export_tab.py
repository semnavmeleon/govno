"""Таб «Экспорт» — качество, антидетект, настройки сохранения."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QFrame,
    QCheckBox, QComboBox, QLabel, QSpinBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..widgets import GlassCard
from ...constants import QUALITY_OPTIONS, BROKEN_DURATION_TYPES


class ExportTab(QScrollArea):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(content)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 8, 6, 0)

        # ── Качество ──
        card1 = GlassCard("Качество кодирования")
        grid = QGridLayout()
        grid.setSpacing(8)

        lbl = QLabel("Качество MP3:")
        lbl.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid.addWidget(lbl, 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(list(QUALITY_OPTIONS.keys()))
        self.quality_combo.setCurrentIndex(0)
        grid.addWidget(self.quality_combo, 0, 1)

        self.chk_bitrate_jitter = QCheckBox("Случайный битрейт (192–320 kbps)")
        self.chk_bitrate_jitter.setToolTip("Каждый файл получит случайный битрейт")
        self.chk_bitrate_jitter.toggled.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.chk_bitrate_jitter, 1, 0, 1, 2)

        card1.setLayout(grid)
        lay.addWidget(card1)

        # ── Антидетект ──
        card2 = GlassCard("Антидетект — файловый уровень")
        grid2 = QGridLayout()
        grid2.setSpacing(8)

        self.chk_frame_shift = QCheckBox("Сдвиг MP3 фреймов (write_xing=0)")
        self.chk_frame_shift.toggled.connect(self._check_conflicts)
        self.chk_frame_shift.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_frame_shift, 0, 0, 1, 2)

        self.chk_broken_duration = QCheckBox("Модифицировать длительность (VBR spoof)")
        self.chk_broken_duration.setToolTip("Изменяет заголовок Xing/Info")
        self.chk_broken_duration.toggled.connect(self._check_conflicts)
        self.chk_broken_duration.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_broken_duration, 1, 0)

        self.broken_combo = QComboBox()
        self.broken_combo.addItems(BROKEN_DURATION_TYPES)
        grid2.addWidget(self.broken_combo, 1, 1)

        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: rgba(255,100,100,0.70); font-size: 11px;")
        self.conflict_label.setWordWrap(True)
        grid2.addWidget(self.conflict_label, 2, 0, 1, 2)

        card2.setLayout(grid2)
        lay.addWidget(card2)

        # ── Обработка ──
        card3 = GlassCard("Обработка")
        grid3 = QGridLayout()
        grid3.setSpacing(8)

        lbl2 = QLabel("Потоков:")
        lbl2.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid3.addWidget(lbl2, 0, 0)
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(2)
        self.workers_spin.setToolTip("Количество параллельных потоков обработки")
        grid3.addWidget(self.workers_spin, 0, 1)

        self.chk_delete_originals = QCheckBox("Удалять оригиналы после обработки")
        self.chk_delete_originals.setStyleSheet("QCheckBox { color: rgba(255,100,100,0.85); }")
        grid3.addWidget(self.chk_delete_originals, 1, 0, 1, 2)

        self.chk_preserve_cover = QCheckBox("Сохранить оригинальную обложку (если режим «Оригинальная»)")
        self.chk_preserve_cover.setChecked(True)
        grid3.addWidget(self.chk_preserve_cover, 2, 0, 1, 2)

        card3.setLayout(grid3)
        lay.addWidget(card3)

        lay.addStretch()
        self.setWidget(content)

    def _check_conflicts(self):
        if self.chk_frame_shift.isChecked() and self.chk_broken_duration.isChecked():
            self.conflict_label.setText(
                "⚠ Сдвиг фреймов и модификация длительности конфликтуют. "
                "Сдвиг фреймов будет отключён при обработке."
            )
        else:
            self.conflict_label.setText("")

    def active_count(self) -> int:
        count = 0
        if self.chk_bitrate_jitter.isChecked(): count += 1
        if self.chk_frame_shift.isChecked(): count += 1
        if self.chk_broken_duration.isChecked(): count += 1
        return count

    def get_settings(self) -> dict:
        quality_keys = list(QUALITY_OPTIONS.values())
        return {
            'quality': quality_keys[self.quality_combo.currentIndex()],
            'bitrate_jitter': self.chk_bitrate_jitter.isChecked(),
            'frame_shift': self.chk_frame_shift.isChecked(),
            'broken_duration_enabled': self.chk_broken_duration.isChecked(),
            'broken_duration_type': self.broken_combo.currentIndex(),
            'max_workers': self.workers_spin.value(),
            'delete_originals': self.chk_delete_originals.isChecked(),
            'preserve_cover': self.chk_preserve_cover.isChecked(),
        }

    def apply_settings(self, s: dict):
        if 'quality' in s:
            vals = list(QUALITY_OPTIONS.values())
            if s['quality'] in vals:
                self.quality_combo.setCurrentIndex(vals.index(s['quality']))
        if 'bitrate_jitter' in s: self.chk_bitrate_jitter.setChecked(s['bitrate_jitter'])
        if 'frame_shift' in s: self.chk_frame_shift.setChecked(s['frame_shift'])
        if 'broken_duration_enabled' in s: self.chk_broken_duration.setChecked(s['broken_duration_enabled'])
        if 'broken_duration_type' in s: self.broken_combo.setCurrentIndex(s['broken_duration_type'])
        if 'max_workers' in s: self.workers_spin.setValue(s['max_workers'])
        if 'delete_originals' in s: self.chk_delete_originals.setChecked(s['delete_originals'])
        if 'preserve_cover' in s: self.chk_preserve_cover.setChecked(s['preserve_cover'])

    def reset_to_defaults(self):
        self.quality_combo.setCurrentIndex(0)
        self.chk_bitrate_jitter.setChecked(False)
        self.chk_frame_shift.setChecked(False)
        self.chk_broken_duration.setChecked(False)
        self.broken_combo.setCurrentIndex(0)
        self.workers_spin.setValue(2)
        self.chk_delete_originals.setChecked(False)
        self.chk_preserve_cover.setChecked(True)
