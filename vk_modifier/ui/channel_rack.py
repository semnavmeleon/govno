"""Панель каналов в стиле FL Studio Channel Rack."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QSlider, QCheckBox, QGridLayout, QScrollArea,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


class ChannelStrip(QFrame):
    """Один канал (слайдер) в стиле FL Studio."""
    
    value_changed = pyqtSignal(float)
    
    def __init__(self, title: str, min_val: float, max_val: float, 
                 neutral: float, step: float = 0.01, 
                 suffix: str = '', decimals: int = 2,
                 color: str = '#00ff88', parent=None):
        super().__init__(parent)
        self.setObjectName('mixerStrip')
        self._min = min_val
        self._max = max_val
        self._neutral = neutral
        self._step = step
        self._suffix = suffix
        self._decimals = decimals
        self._color = QColor(color)
        
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(6)
        
        # Заголовок
        self._title_label = QLabel(title.upper())
        self._title_label.setStyleSheet(f"""
            QLabel {{
                color: {self._color.name()};
                font-size: 9px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self._title_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._title_label)
        
        # Вертикальный слайдер
        self._slider = QSlider(Qt.Vertical)
        steps = int((self._max - self._min) / self._step)
        self._slider.setRange(0, steps)
        self._slider.setValue(self._val_to_pos(self._neutral))
        self._slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                background: #1a1a1a;
                width: 6px;
                border-radius: 3px;
                border: 1px solid #2a2a2a;
            }}
            QSlider::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._color.name()}, stop:1 {self._color.darker(120).name()});
                width: 16px;
                height: 14px;
                margin: 0 -5px;
                border-radius: 3px;
                border: 1px solid #004422;
            }}
            QSlider::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #44ffaa, stop:1 {self._color.name()});
            }}
            QSlider::sub-page:vertical {{
                background: {self._color.darker(120).name()};
                border-radius: 3px;
            }}
        """)
        self._slider.valueChanged.connect(self._on_value_changed)
        lay.addWidget(self._slider, 1)
        
        # Значение
        self._value_label = QLabel(self._format_value(self._neutral))
        self._value_label.setStyleSheet("""
            QLabel {
                color: #909090;
                font-size: 9px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }
        """)
        self._value_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._value_label)
        
    def _val_to_pos(self, val: float) -> int:
        return round((val - self._min) / self._step)
        
    def _pos_to_val(self, pos: int) -> float:
        return self._min + pos * self._step
        
    def _format_value(self, val: float) -> str:
        if self._decimals == 0:
            return f"{int(val)}{self._suffix}"
        return f"{val:.{self._decimals}f}{self._suffix}"
        
    def _on_value_changed(self, pos: int):
        val = self._pos_to_val(pos)
        active = abs(val - self._neutral) > self._step * 0.5
        
        if active:
            self._value_label.setStyleSheet(f"""
                QLabel {{
                    color: {self._color.name()};
                    font-size: 9px;
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
        else:
            self._value_label.setStyleSheet("""
                QLabel {
                    color: #909090;
                    font-size: 9px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }
            """)
            
        self._value_label.setText(self._format_value(val))
        self.value_changed.emit(val)
        
    def value(self) -> float:
        return self._pos_to_val(self._slider.value())
        
    def setValue(self, val: float):
        self._slider.setValue(self._val_to_pos(val))
        
    def is_active(self) -> bool:
        return abs(self.value() - self._neutral) > self._step * 0.5
        
    def reset(self):
        self.setValue(self._neutral)


class ChannelRack(QScrollArea):
    """
    Панель каналов в стиле FL Studio Channel Rack.
    Содержит вертикальные слайдеры для управления параметрами.
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background: #242424;
                border: none;
            }
        """)
        
        self._setup_ui()
        
    def _setup_ui(self):
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        
        # Заголовок
        header = QLabel("🎛️ CHANNEL RACK")
        header.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background: #1a1a1a;
                border-radius: 4px;
            }
        """)
        lay.addWidget(header)
        
        # Сетка каналов
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Каналы эффектов
        self.channels = {}
        
        # Row 0: Pitch & Speed
        self.channels['pitch'] = ChannelStrip(
            "PITCH", -2.0, 2.0, 0.0, 0.5, " пт", 1, '#00ff88'
        )
        self.channels['pitch'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['pitch'], 0, 0)
        
        self.channels['speed'] = ChannelStrip(
            "SPEED", 0.95, 1.05, 1.0, 0.005, "x", 3, '#00bcd4'
        )
        self.channels['speed'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['speed'], 0, 1)
        
        # Row 1: Phase & Noise
        self.channels['phase'] = ChannelStrip(
            "PHASE", 0.0, 1.0, 0.0, 0.1, " мс", 1, '#ff9800'
        )
        self.channels['phase'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['phase'], 0, 2)
        
        self.channels['noise'] = ChannelStrip(
            "NOISE", 0.0, 0.01, 0.0, 0.0005, "", 4, '#ff5252'
        )
        self.channels['noise'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['noise'], 0, 3)
        
        # Row 2: Fade In/Out
        self.channels['fade_in'] = ChannelStrip(
            "FADE IN", 0, 30, 0, 1, " сек", 0, '#9c27b0'
        )
        self.channels['fade_in'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['fade_in'], 1, 0)
        
        self.channels['fade_out'] = ChannelStrip(
            "FADE OUT", 0, 30, 0, 1, " сек", 0, '#9c27b0'
        )
        self.channels['fade_out'].value_changed.connect(self._on_change)
        grid.addWidget(self.channels['fade_out'], 1, 1)
        
        lay.addLayout(grid)
        
        # Переключатели эффектов
        effects_frame = QFrame()
        effects_frame.setObjectName('mixerStrip')
        effects_lay = QVBoxLayout(effects_frame)
        effects_lay.setContentsMargins(8, 8, 8, 8)
        effects_lay.setSpacing(6)
        
        effects_title = QLabel("⚡ EFFECTS")
        effects_title.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
            }
        """)
        effects_lay.addWidget(effects_title)
        
        self.chk_eq = QCheckBox("🎚️ Эквализация")
        self.chk_eq.setStyleSheet(self._checkbox_style('#00ff88'))
        self.chk_eq.toggled.connect(self._on_change)
        effects_lay.addWidget(self.chk_eq)
        
        self.eq_combo = QComboBox()
        self.eq_combo.addItems([
            "Лёгкая коррекция",
            "Средняя коррекция", 
            "Сильная коррекция",
            "Boost середины",
            "Boost верхов",
        ])
        self.eq_combo.setCurrentIndex(1)
        self.eq_combo.setEnabled(False)
        self.eq_combo.currentIndexChanged.connect(self._on_change)
        effects_lay.addWidget(self.eq_combo)
        
        self.chk_compression = QCheckBox("📊 Компрессия")
        self.chk_compression.setStyleSheet(self._checkbox_style('#00bcd4'))
        self.chk_compression.toggled.connect(self._on_change)
        effects_lay.addWidget(self.chk_compression)
        
        self.chk_ultrasound = QCheckBox("🔊 Ультразвук (19-22kHz)")
        self.chk_ultrasound.setStyleSheet(self._checkbox_style('#ff9800'))
        self.chk_ultrasound.toggled.connect(self._on_change)
        effects_lay.addWidget(self.chk_ultrasound)
        
        self.chk_dc_shift = QCheckBox("📡 DC сдвиг")
        self.chk_dc_shift.setStyleSheet(self._checkbox_style('#ff5252'))
        self.chk_dc_shift.toggled.connect(self._on_change)
        effects_lay.addWidget(self.chk_dc_shift)
        
        lay.addWidget(effects_frame)
        
        lay.addStretch()
        self.setWidget(content)
        
    def _checkbox_style(self, color: str) -> str:
        return f"""
            QCheckBox {{
                spacing: 8px;
                color: {color};
                font-size: 11px;
                font-weight: 600;
                padding: 4px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                background: #1a1a1a;
                border: 2px solid {color};
            }}
            QCheckBox::indicator:checked {{
                background: {color};
            }}
        """
        
    def _on_change(self):
        # EQ combo enable/disable
        self.eq_combo.setEnabled(self.chk_eq.isChecked())
        self.settings_changed.emit()
        
    def active_count(self) -> int:
        count = 0
        for channel in self.channels.values():
            if channel.is_active():
                count += 1
        if self.chk_eq.isChecked():
            count += 1
        if self.chk_compression.isChecked():
            count += 1
        if self.chk_ultrasound.isChecked():
            count += 1
        if self.chk_dc_shift.isChecked():
            count += 1
        return count
        
    def get_settings(self) -> dict:
        return {
            'pitch_semitones': self.channels['pitch'].value(),
            'speed_factor': self.channels['speed'].value(),
            'eq_preset_index': self.eq_combo.currentIndex() if self.chk_eq.isChecked() else -1,
            'compression_enabled': self.chk_compression.isChecked(),
            'phase_delay_ms': self.channels['phase'].value(),
            'noise_amplitude': self.channels['noise'].value(),
            'ultrasound_enabled': self.chk_ultrasound.isChecked(),
            'dc_shift_enabled': self.chk_dc_shift.isChecked(),
            'fade_in_sec': int(self.channels['fade_in'].value()),
            'fade_out_sec': int(self.channels['fade_out'].value()),
        }
        
    def apply_settings(self, s: dict):
        if 'pitch_semitones' in s:
            self.channels['pitch'].setValue(s['pitch_semitones'])
        if 'speed_factor' in s:
            self.channels['speed'].setValue(s['speed_factor'])
        if 'eq_preset_index' in s:
            idx = s['eq_preset_index']
            self.chk_eq.setChecked(idx >= 0)
            if idx >= 0:
                self.eq_combo.setCurrentIndex(idx)
        if 'compression_enabled' in s:
            self.chk_compression.setChecked(s['compression_enabled'])
        if 'phase_delay_ms' in s:
            self.channels['phase'].setValue(s['phase_delay_ms'])
        if 'noise_amplitude' in s:
            self.channels['noise'].setValue(s['noise_amplitude'])
        if 'ultrasound_enabled' in s:
            self.chk_ultrasound.setChecked(s['ultrasound_enabled'])
        if 'dc_shift_enabled' in s:
            self.chk_dc_shift.setChecked(s['dc_shift_enabled'])
        if 'fade_in_sec' in s:
            self.channels['fade_in'].setValue(s['fade_in_sec'])
        if 'fade_out_sec' in s:
            self.channels['fade_out'].setValue(s['fade_out_sec'])
            
    def reset_to_defaults(self):
        for channel in self.channels.values():
            channel.reset()
        self.chk_eq.setChecked(False)
        self.chk_compression.setChecked(False)
        self.chk_ultrasound.setChecked(False)
        self.chk_dc_shift.setChecked(False)
        self.eq_combo.setCurrentIndex(0)
