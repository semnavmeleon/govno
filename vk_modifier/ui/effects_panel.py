"""Панель эффектов."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QSlider, QCheckBox, QComboBox, QGridLayout, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal


class VerticalSlider(QWidget):
    """Вертикальный слайдер с подписью."""
    
    value_changed = pyqtSignal(float)
    
    def __init__(self, title, min_val, max_val, default, suffix=''):
        super().__init__()
        self._min = min_val
        self._max = max_val
        self._default = default
        self._suffix = suffix
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(5)
        
        # Заголовок
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #00adb5; font-size: 10px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Слайдер
        self.slider = QSlider(Qt.Vertical)
        steps = int((max_val - min_val) * 100)
        self.slider.setRange(0, steps)
        self.slider.setValue(int((default - min_val) * 100))
        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #1a1a2e;
                width: 6px;
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00adb5, stop:1 #e94560);
                height: 16px;
                width: 16px;
                margin: 0 -5px;
                border-radius: 4px;
            }
            QSlider::sub-page:vertical {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #00adb5, stop:1 #e94560);
                border-radius: 3px;
            }
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, 1)
        
        # Значение
        self.value_label = QLabel(self._format_value(default))
        self.value_label.setStyleSheet("color: #a0a0a0; font-size: 9px; font-family: 'Consolas';")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
    def _format_value(self, value):
        val = self._min + value / 100 * (self._max - self._min)
        if abs(val) < 10:
            return f"{val:.2f}{self._suffix}"
        return f"{int(val)}{self._suffix}"
        
    def _on_value_changed(self, value):
        self.value_label.setText(self._format_value(value))
        self.value_changed.emit(self.value())
        
    def value(self):
        return self._min + self.slider.value() / 100 * (self._max - self._min)
        
    def setValue(self, value):
        pos = int((value - self._min) * 100)
        self.slider.setValue(pos)


class EffectsPanel(QScrollArea):
    """Панель управления эффектами."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Заголовок
        header = QLabel("🎛️ ЭФФЕКТЫ")
        header.setObjectName('headerLabel')
        layout.addWidget(header)
        
        # Слайдеры
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(10)
        
        self.pitch_slider = VerticalSlider("PITCH", -2, 2, 0, ' пт')
        self.pitch_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.pitch_slider, 1)
        
        self.speed_slider = VerticalSlider("SPEED", 0.95, 1.05, 1.0, 'x')
        self.speed_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.speed_slider, 1)
        
        self.phase_slider = VerticalSlider("PHASE", 0, 1, 0, ' мс')
        self.phase_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.phase_slider, 1)
        
        self.noise_slider = VerticalSlider("NOISE", 0, 0.01, 0, '')
        self.noise_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.noise_slider, 1)
        
        self.fade_in_slider = VerticalSlider("FADE IN", 0, 30, 0, ' сек')
        self.fade_in_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.fade_in_slider, 1)
        
        self.fade_out_slider = VerticalSlider("FADE OUT", 0, 30, 0, ' сек')
        self.fade_out_slider.value_changed.connect(self.settings_changed)
        sliders_layout.addWidget(self.fade_out_slider, 1)
        
        layout.addLayout(sliders_layout)
        
        # Чекбоксы эффектов
        effects_frame = QFrame()
        effects_frame.setObjectName('cardFrame')
        effects_layout = QVBoxLayout(effects_frame)
        effects_layout.setSpacing(8)
        
        effects_title = QLabel("⚡ ДОПОЛНИТЕЛЬНЫЕ ЭФФЕКТЫ")
        effects_title.setObjectName('sectionLabel')
        effects_layout.addWidget(effects_title)
        
        self.chk_eq = QCheckBox("🎚️ Эквализация")
        self.chk_eq.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.chk_eq.toggled.connect(self.settings_changed)
        effects_layout.addWidget(self.chk_eq)
        
        self.eq_combo = QComboBox()
        self.eq_combo.addItems([
            "Лёгкая коррекция",
            "Средняя коррекция",
            "Сильная коррекция",
            "Boost середины",
            "Boost верхов",
        ])
        self.eq_combo.setEnabled(False)
        self.eq_combo.currentIndexChanged.connect(self.settings_changed)
        effects_layout.addWidget(self.eq_combo)
        
        self.chk_compression = QCheckBox("📊 Компрессия")
        self.chk_compression.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.chk_compression.toggled.connect(self.settings_changed)
        effects_layout.addWidget(self.chk_compression)
        
        self.chk_ultrasound = QCheckBox("🔊 Ультразвук (19-22kHz)")
        self.chk_ultrasound.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.chk_ultrasound.toggled.connect(self.settings_changed)
        effects_layout.addWidget(self.chk_ultrasound)
        
        self.chk_dc_shift = QCheckBox("📡 DC сдвиг")
        self.chk_dc_shift.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.chk_dc_shift.toggled.connect(self.settings_changed)
        effects_layout.addWidget(self.chk_dc_shift)
        
        layout.addWidget(effects_frame)
        
        layout.addStretch()
        self.setWidget(content)
        
    def get_settings(self):
        return {
            'pitch_semitones': self.pitch_slider.value(),
            'speed_factor': self.speed_slider.value(),
            'eq_preset_index': self.eq_combo.currentIndex() if self.chk_eq.isChecked() else -1,
            'compression_enabled': self.chk_compression.isChecked(),
            'phase_delay_ms': self.phase_slider.value(),
            'noise_amplitude': self.noise_slider.value(),
            'ultrasound_enabled': self.chk_ultrasound.isChecked(),
            'dc_shift_enabled': self.chk_dc_shift.isChecked(),
            'fade_in_sec': int(self.fade_in_slider.value()),
            'fade_out_sec': int(self.fade_out_slider.value()),
        }
