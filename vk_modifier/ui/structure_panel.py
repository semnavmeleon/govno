"""Панель структуры трека."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QSpinBox, QCheckBox, QPushButton, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal


class StructurePanelWidget(QFrame):
    """Панель управления структурой трека."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName('cardFrame')
        
        self._duration = 0.0
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Заголовок
        header = QLabel("📋 СТРУКТУРА")
        header.setObjectName('headerLabel')
        layout.addWidget(header)
        
        # Обрезка
        trim_layout = QHBoxLayout()
        trim_layout.setSpacing(10)
        
        trim_label = QLabel("✂️ Обрезать начало:")
        trim_label.setStyleSheet("color: #ffaa00; font-size: 12px; font-weight: bold;")
        trim_layout.addWidget(trim_label)
        
        self.trim_spin = QSpinBox()
        self.trim_spin.setRange(0, 9999)
        self.trim_spin.setValue(0)
        self.trim_spin.setSuffix(" сек")
        self.trim_spin.setStyleSheet("""
            QSpinBox {
                background: #1a1a2e;
                border: 2px solid #2a2a3e;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox:hover {
                border-color: #ffaa00;
            }
        """)
        self.trim_spin.valueChanged.connect(self.settings_changed)
        trim_layout.addWidget(self.trim_spin, 1)
        
        layout.addLayout(trim_layout)
        
        # Вырезка
        cut_layout = QVBoxLayout()
        cut_layout.setSpacing(8)
        
        cut_label = QLabel("🔪 Вырезать фрагмент:")
        cut_label.setStyleSheet("color: #ff4757; font-size: 12px; font-weight: bold;")
        cut_layout.addWidget(cut_label)
        
        cut_row = QHBoxLayout()
        cut_row.setSpacing(10)
        
        cut_from_label = QLabel("От:")
        cut_from_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        cut_row.addWidget(cut_from_label)
        
        self.cut_start_spin = QSpinBox()
        self.cut_start_spin.setRange(0, 9999)
        self.cut_start_spin.setValue(0)
        self.cut_start_spin.setSuffix(" сек")
        self.cut_start_spin.setStyleSheet("""
            QSpinBox {
                background: #1a1a2e;
                border: 2px solid #2a2a3e;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox:hover {
                border-color: #ff4757;
            }
        """)
        self.cut_start_spin.valueChanged.connect(self.settings_changed)
        cut_row.addWidget(self.cut_start_spin, 1)
        
        cut_to_label = QLabel("До:")
        cut_to_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        cut_row.addWidget(cut_to_label)
        
        self.cut_end_spin = QSpinBox()
        self.cut_end_spin.setRange(0, 9999)
        self.cut_end_spin.setValue(0)
        self.cut_end_spin.setSuffix(" сек")
        self.cut_end_spin.setStyleSheet("""
            QSpinBox {
                background: #1a1a2e;
                border: 2px solid #2a2a3e;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox:hover {
                border-color: #ff4757;
            }
        """)
        self.cut_end_spin.valueChanged.connect(self.settings_changed)
        cut_row.addWidget(self.cut_end_spin, 1)
        
        cut_layout.addLayout(cut_row)
        layout.addLayout(cut_layout)
        
        # Тишина
        silence_layout = QHBoxLayout()
        silence_layout.setSpacing(10)
        
        silence_label = QLabel("➕ Тишина в конец:")
        silence_label.setStyleSheet("color: #00adb5; font-size: 12px; font-weight: bold;")
        silence_layout.addWidget(silence_label)
        
        self.silence_spin = QSpinBox()
        self.silence_spin.setRange(0, 999)
        self.silence_spin.setValue(0)
        self.silence_spin.setSuffix(" сек")
        self.silence_spin.setStyleSheet("""
            QSpinBox {
                background: #1a1a2e;
                border: 2px solid #2a2a3e;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox:hover {
                border-color: #00adb5;
            }
        """)
        self.silence_spin.valueChanged.connect(self.settings_changed)
        silence_layout.addWidget(self.silence_spin, 1)
        
        layout.addLayout(silence_layout)
        
        # Инфо о длительности
        self.duration_info = QLabel("")
        self.duration_info.setStyleSheet("""
            color: #ffaa00;
            font-size: 11px;
            padding: 8px;
            background: rgba(255, 170, 0, 0.1);
            border-radius: 6px;
        """)
        self.duration_info.setWordWrap(True)
        self.duration_info.setVisible(False)
        layout.addWidget(self.duration_info)
        
        layout.addStretch()
        
    def set_duration(self, duration):
        """Установить длительность трека."""
        self._duration = duration
        self._update_info()
        
    def set_marker(self, marker_type, value):
        """Установить маркер."""
        if marker_type == 'trim':
            self.trim_spin.setValue(int(value))
        elif marker_type == 'cut_start':
            self.cut_start_spin.setValue(int(value))
        elif marker_type == 'cut_end':
            self.cut_end_spin.setValue(int(value))
            
    def _update_info(self):
        """Обновить информацию."""
        if self._duration <= 0:
            self.duration_info.setVisible(False)
            return
            
        trim = self.trim_spin.value()
        cut_start = self.cut_start_spin.value()
        cut_end = self.cut_end_spin.value()
        cut_len = (cut_end - cut_start) if cut_end > cut_start > 0 else 0
        
        remaining = self._duration - trim - cut_len
        
        if trim >= self._duration:
            self.duration_info.setText("⚠ Обрезка больше длительности трека!")
            self.duration_info.setVisible(True)
        elif remaining < 1:
            self.duration_info.setText(f"⚠ Останется меньше 1 секунды ({remaining:.1f}с)")
            self.duration_info.setVisible(True)
        else:
            self.duration_info.setText(
                f"ℹ Оригинал: {self._duration:.1f}с → После обрезки: {remaining:.1f}с"
            )
            self.duration_info.setVisible(True)
            
    def get_settings(self):
        return {
            'trim_start_sec': self.trim_spin.value(),
            'cut_start_sec': float(self.cut_start_spin.value()),
            'cut_end_sec': float(self.cut_end_spin.value()),
            'silence_end_sec': self.silence_spin.value(),
        }
