"""Таб «Структура» — обрезка, вырезка, сращивание, волна."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QFrame,
    QCheckBox, QSpinBox, QLabel, QPushButton, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..widgets import GlassCard, SliderWithLabel, WaveformWidget


GLASS_BTN = """
    QPushButton {
        background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px; padding: 10px 18px;
        color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500;
    }
    QPushButton:hover { background: rgba(255,255,255,0.10); border-color: rgba(255,255,255,0.18); }
    QPushButton:pressed { background: rgba(255,255,255,0.03); }
    QPushButton:disabled {
        background: rgba(255,255,255,0.02); color: rgba(255,255,255,0.20);
        border-color: rgba(255,255,255,0.04);
    }
"""


class StructureTab(QScrollArea):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._merge_path = ''
        self._track_duration = 0.0

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(content)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 8, 6, 0)

        # ── Волна ──
        self.waveform = WaveformWidget()
        self.waveform.position_clicked.connect(self._on_waveform_click)
        lay.addWidget(self.waveform)

        # ── Предупреждение о длительности ──
        self.duration_warning = QLabel("")
        self.duration_warning.setWordWrap(True)
        self.duration_warning.setStyleSheet(
            "color: rgba(255,200,50,0.85); font-size: 12px; padding: 4px 8px;"
        )
        self.duration_warning.setVisible(False)
        lay.addWidget(self.duration_warning)

        # ── Обрезка ──
        card1 = GlassCard("Обрезка")
        grid = QVBoxLayout()
        grid.setSpacing(12)

        self.slider_trim = SliderWithLabel(
            "Обрезать начало:", 0, 30, neutral=0, step=1,
            suffix=" сек", decimals=0
        )
        self.slider_trim.valueChanged.connect(self._on_setting_changed)
        grid.addWidget(self.slider_trim)

        # Вырезка — два поля с секундами
        cut_label = QLabel("Вырезать фрагмент (начало и конец в секундах):")
        cut_label.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px;")
        grid.addWidget(cut_label)

        cut_row = QWidget()
        cut_lay = QGridLayout(cut_row)
        cut_lay.setContentsMargins(0, 0, 0, 0)
        cut_lay.setSpacing(8)

        lbl_from = QLabel("От:")
        lbl_from.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px;")
        cut_lay.addWidget(lbl_from, 0, 0)
        self.cut_start_spin = QSpinBox()
        self.cut_start_spin.setRange(0, 9999)
        self.cut_start_spin.setValue(0)
        self.cut_start_spin.setSuffix(" сек")
        self.cut_start_spin.valueChanged.connect(self._on_setting_changed)
        cut_lay.addWidget(self.cut_start_spin, 0, 1)

        lbl_to = QLabel("До:")
        lbl_to.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px;")
        cut_lay.addWidget(lbl_to, 0, 2)
        self.cut_end_spin = QSpinBox()
        self.cut_end_spin.setRange(0, 9999)
        self.cut_end_spin.setValue(0)
        self.cut_end_spin.setSuffix(" сек")
        self.cut_end_spin.valueChanged.connect(self._on_setting_changed)
        cut_lay.addWidget(self.cut_end_spin, 0, 3)

        grid.addWidget(cut_row)

        card1.setLayout(grid)
        lay.addWidget(card1)

        # ── Добавление ──
        card2 = GlassCard("Добавление")
        grid2 = QVBoxLayout()
        grid2.setSpacing(12)

        self.slider_silence = SliderWithLabel(
            "Тишина в конец:", 0, 300, neutral=0, step=5,
            suffix=" сек", decimals=0
        )
        self.slider_silence.valueChanged.connect(self._on_setting_changed)
        grid2.addWidget(self.slider_silence)

        self.chk_merge = QCheckBox("Сращивание с другим треком")
        self.chk_merge.toggled.connect(self._on_merge_toggled)
        self.chk_merge.toggled.connect(self._on_setting_changed)
        grid2.addWidget(self.chk_merge)

        self.btn_merge = QPushButton("Выбрать трек для сращивания")
        self.btn_merge.setStyleSheet(GLASS_BTN)
        self.btn_merge.setEnabled(False)
        self.btn_merge.clicked.connect(self._select_merge)
        grid2.addWidget(self.btn_merge)

        self.merge_label = QLabel("")
        self.merge_label.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 11px; font-style: italic;")
        grid2.addWidget(self.merge_label)

        card2.setLayout(grid2)
        lay.addWidget(card2)

        lay.addStretch()
        self.setWidget(content)

    def load_track_waveform(self, file_path: str):
        """Загрузить волну для указанного трека."""
        self.waveform.load_track(file_path)

    def set_track_duration(self, duration_sec: float):
        """Установить длительность трека для валидации."""
        self._track_duration = duration_sec
        self._validate_duration()

    def _on_setting_changed(self):
        self.settings_changed.emit()
        self._update_waveform_markers()
        self._validate_duration()

    def _update_waveform_markers(self):
        self.waveform.set_markers(
            trim_start=self.slider_trim.value(),
            cut_start=float(self.cut_start_spin.value()),
            cut_end=float(self.cut_end_spin.value()),
        )

    def _validate_duration(self):
        """Проверить что обрезка не превышает длительность трека."""
        if self._track_duration <= 0:
            self.duration_warning.setVisible(False)
            return

        dur = self._track_duration
        trim = self.slider_trim.value()
        cut_s = self.cut_start_spin.value()
        cut_e = self.cut_end_spin.value()
        cut_len = (cut_e - cut_s) if cut_e > cut_s > 0 else 0

        remaining = dur - trim - cut_len
        warnings = []

        if trim >= dur:
            warnings.append(f"Обрезка начала ({trim}с) >= длительность трека ({dur:.1f}с)")
        elif remaining < 1:
            warnings.append(f"После обрезки останется < 1 секунды ({remaining:.1f}с)")
        elif remaining < 5:
            warnings.append(f"После обрезки останется только {remaining:.1f}с")

        if cut_s > 0 and cut_e > 0 and cut_e <= cut_s:
            warnings.append("Конец вырезки должен быть больше начала")
        if cut_e > dur:
            warnings.append(f"Конец вырезки ({cut_e}с) > длительность ({dur:.1f}с)")

        if warnings:
            self.duration_warning.setText("⚠ " + " · ".join(warnings))
            self.duration_warning.setVisible(True)
        else:
            self.duration_warning.setVisible(False)

    def _on_waveform_click(self, seconds):
        """Клик по волне — подставить в поле обрезки."""
        self.slider_trim.setValue(int(seconds))

    def _on_merge_toggled(self, checked):
        self.btn_merge.setEnabled(checked)
        if not checked:
            self._merge_path = ''
            self.merge_label.setText('')

    def _select_merge(self):
        path, _ = QFileDialog.getOpenFileName(self, "Трек для сращивания", "", "MP3 (*.mp3)")
        if path:
            self._merge_path = path
            self.merge_label.setText(f"Выбран: {os.path.basename(path)}")

    def active_count(self) -> int:
        count = 0
        if self.slider_trim.is_active(): count += 1
        if self.cut_start_spin.value() > 0 and self.cut_end_spin.value() > 0: count += 1
        if self.slider_silence.is_active(): count += 1
        if self.chk_merge.isChecked(): count += 1
        return count

    def get_settings(self) -> dict:
        return {
            'trim_start_sec': int(self.slider_trim.value()),
            'cut_start_sec': float(self.cut_start_spin.value()),
            'cut_end_sec': float(self.cut_end_spin.value()),
            'silence_end_sec': int(self.slider_silence.value()),
            'merge_enabled': self.chk_merge.isChecked(),
            'merge_track_path': self._merge_path if self.chk_merge.isChecked() else '',
        }

    def apply_settings(self, s: dict):
        if 'trim_start_sec' in s: self.slider_trim.setValue(s['trim_start_sec'])
        if 'cut_start_sec' in s: self.cut_start_spin.setValue(int(s['cut_start_sec']))
        if 'cut_end_sec' in s: self.cut_end_spin.setValue(int(s['cut_end_sec']))
        if 'silence_end_sec' in s: self.slider_silence.setValue(s['silence_end_sec'])
        if 'merge_enabled' in s: self.chk_merge.setChecked(s['merge_enabled'])

    def reset_to_defaults(self):
        self.slider_trim.setValue(0)
        self.cut_start_spin.setValue(0)
        self.cut_end_spin.setValue(0)
        self.slider_silence.setValue(0)
        self.chk_merge.setChecked(False)
        self.duration_warning.setVisible(False)
