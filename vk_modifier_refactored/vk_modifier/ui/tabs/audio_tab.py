"""Таб «Аудио» — слайдеры вместо чекбоксов для параметрических эффектов."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea,
    QFrame, QCheckBox, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..widgets import GlassCard, SliderWithLabel


class AudioTab(QScrollArea):
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

        # ── Высота и скорость ──
        card1 = GlassCard("Высота и скорость")
        grid = QVBoxLayout()
        grid.setSpacing(12)

        self.slider_pitch = SliderWithLabel(
            "Тональность:", -2.0, 2.0, neutral=0.0, step=0.5,
            suffix=" пт", decimals=1
        )
        self.slider_pitch.valueChanged.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.slider_pitch)

        self.slider_speed = SliderWithLabel(
            "Скорость:", 0.95, 1.05, neutral=1.0, step=0.005,
            suffix="x", decimals=3
        )
        self.slider_speed.valueChanged.connect(lambda: self.settings_changed.emit())
        grid.addWidget(self.slider_speed)

        card1.setLayout(grid)
        lay.addWidget(card1)

        # ── Эквализация и динамика ──
        card2 = GlassCard("Эквализация и динамика")
        grid2 = QGridLayout()
        grid2.setSpacing(8)

        self.chk_eq = QCheckBox("Эквализация")
        self.chk_eq.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_eq, 0, 0)
        self.eq_combo = QComboBox()
        self.eq_combo.addItems([
            "Лёгкая коррекция", "Средняя коррекция", "Сильная коррекция",
            "Boost середины", "Boost верхов",
        ])
        self.eq_combo.setCurrentIndex(1)
        grid2.addWidget(self.eq_combo, 0, 1)

        self.chk_compression = QCheckBox("Динамическая компрессия")
        self.chk_compression.setToolTip("Уменьшает разницу между тихим и громким")
        self.chk_compression.toggled.connect(lambda: self.settings_changed.emit())
        grid2.addWidget(self.chk_compression, 1, 0, 1, 2)

        card2.setLayout(grid2)
        lay.addWidget(card2)

        # ── Эффекты и шум ──
        card3 = GlassCard("Эффекты и шум")
        grid3 = QVBoxLayout()
        grid3.setSpacing(12)

        self.slider_phase = SliderWithLabel(
            "Фазовый сдвиг:", 0.0, 1.0, neutral=0.0, step=0.1,
            suffix=" мс", decimals=1
        )
        self.slider_phase.valueChanged.connect(lambda: self.settings_changed.emit())
        grid3.addWidget(self.slider_phase)

        self.slider_noise = SliderWithLabel(
            "Розовый шум:", 0.0, 0.01, neutral=0.0, step=0.0005,
            suffix="", decimals=4
        )
        self.slider_noise.valueChanged.connect(lambda: self.settings_changed.emit())
        grid3.addWidget(self.slider_noise)

        self.chk_ultrasound = QCheckBox("Ультразвуковой шум (19–22kHz)")
        self.chk_ultrasound.setToolTip("Неслышимый тон, меняющий хеш файла")
        self.chk_ultrasound.toggled.connect(lambda: self.settings_changed.emit())
        grid3.addWidget(self.chk_ultrasound)

        self.chk_dc_shift = QCheckBox("DC сдвиг")
        self.chk_dc_shift.setToolTip("Микросдвиг постоянной составляющей сигнала")
        self.chk_dc_shift.toggled.connect(lambda: self.settings_changed.emit())
        grid3.addWidget(self.chk_dc_shift)

        card3.setLayout(grid3)
        lay.addWidget(card3)

        # ── Fade ──
        card4 = GlassCard("Плавные переходы")
        grid4 = QVBoxLayout()
        grid4.setSpacing(12)

        self.slider_fade_in = SliderWithLabel(
            "Fade in:", 0, 30, neutral=0, step=1,
            suffix=" сек", decimals=0
        )
        self.slider_fade_in.valueChanged.connect(lambda: self.settings_changed.emit())
        grid4.addWidget(self.slider_fade_in)

        self.slider_fade_out = SliderWithLabel(
            "Fade out:", 0, 30, neutral=0, step=1,
            suffix=" сек", decimals=0
        )
        self.slider_fade_out.valueChanged.connect(lambda: self.settings_changed.emit())
        grid4.addWidget(self.slider_fade_out)

        card4.setLayout(grid4)
        lay.addWidget(card4)

        lay.addStretch()
        self.setWidget(content)

    def active_count(self) -> int:
        """Количество активных эффектов."""
        count = 0
        if self.slider_pitch.is_active(): count += 1
        if self.slider_speed.is_active(): count += 1
        if self.chk_eq.isChecked(): count += 1
        if self.chk_compression.isChecked(): count += 1
        if self.slider_phase.is_active(): count += 1
        if self.slider_noise.is_active(): count += 1
        if self.chk_ultrasound.isChecked(): count += 1
        if self.chk_dc_shift.isChecked(): count += 1
        if self.slider_fade_in.is_active(): count += 1
        if self.slider_fade_out.is_active(): count += 1
        return count

    def get_settings(self) -> dict:
        return {
            'pitch_semitones': self.slider_pitch.value(),
            'speed_factor': self.slider_speed.value(),
            'eq_preset_index': self.eq_combo.currentIndex() if self.chk_eq.isChecked() else -1,
            'compression_enabled': self.chk_compression.isChecked(),
            'phase_delay_ms': self.slider_phase.value(),
            'noise_amplitude': self.slider_noise.value(),
            'ultrasound_enabled': self.chk_ultrasound.isChecked(),
            'dc_shift_enabled': self.chk_dc_shift.isChecked(),
            'fade_in_sec': int(self.slider_fade_in.value()),
            'fade_out_sec': int(self.slider_fade_out.value()),
        }

    def apply_settings(self, s: dict):
        if 'pitch_semitones' in s: self.slider_pitch.setValue(s['pitch_semitones'])
        if 'speed_factor' in s: self.slider_speed.setValue(s['speed_factor'])
        if 'eq_preset_index' in s:
            idx = s['eq_preset_index']
            self.chk_eq.setChecked(idx >= 0)
            if idx >= 0: self.eq_combo.setCurrentIndex(idx)
        if 'compression_enabled' in s: self.chk_compression.setChecked(s['compression_enabled'])
        if 'phase_delay_ms' in s: self.slider_phase.setValue(s['phase_delay_ms'])
        if 'noise_amplitude' in s: self.slider_noise.setValue(s['noise_amplitude'])
        if 'ultrasound_enabled' in s: self.chk_ultrasound.setChecked(s['ultrasound_enabled'])
        if 'dc_shift_enabled' in s: self.chk_dc_shift.setChecked(s['dc_shift_enabled'])
        if 'fade_in_sec' in s: self.slider_fade_in.setValue(s['fade_in_sec'])
        if 'fade_out_sec' in s: self.slider_fade_out.setValue(s['fade_out_sec'])

    def reset_to_defaults(self):
        self.slider_pitch.setValue(0.0)
        self.slider_speed.setValue(1.0)
        self.chk_eq.setChecked(False)
        self.chk_compression.setChecked(False)
        self.slider_phase.setValue(0.0)
        self.slider_noise.setValue(0.0)
        self.chk_ultrasound.setChecked(False)
        self.chk_dc_shift.setChecked(False)
        self.slider_fade_in.setValue(0)
        self.slider_fade_out.setValue(0)
