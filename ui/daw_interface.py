"""DAW Interface — ПОЛНАЯ копия asdas.html с расширенными стилями."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QSlider, QCheckBox, QComboBox, QLineEdit, QScrollArea,
    QSplitter, QFileDialog, QProgressBar, QDoubleSpinBox, QSizePolicy,
    QGraphicsDropShadowEffect, QGraphicsBlurEffect, QGraphicsOpacityEffect,
    QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize, QRect
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QRadialGradient, 
    QPainter, QPen, QBrush, QFontDatabase, QCursor, QIcon,
    QPainterPath, QTransform, QGradient
)


# ══════════════════════════════════════════════════════════════════════════════
#  ПОЛНЫЕ СТИЛИ ИЗ asdas.html
# ══════════════════════════════════════════════════════════════════════════════

DAW_STYLESHEET = """
/* ═══════════════════════════════════════════════════════════════════════════ */
/*  GLOBAL STYLES                                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

* {
    font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
    outline: none;
    selection-background-color: rgba(59, 130, 246, 0.3);
}

QMainWindow {
    background: qlineargradient(
        x1: 0.5, y1: 0, x2: 0.5, y2: 1,
        stop: 0 #1e1b4b,
        stop: 0.35 #0f172a,
        stop: 1 #020617
    );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CUSTOM SCROLLBAR                                                            */
/* ═══════════════════════════════════════════════════════════════════════════ */

QScrollBar:vertical {
    background: rgba(30, 41, 59, 0.5);
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #475569, stop: 1 #64748b);
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #64748b, stop: 1 #94a3b8);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: rgba(30, 41, 59, 0.5);
    height: 6px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #475569, stop: 1 #64748b);
    border-radius: 3px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #64748b, stop: 1 #94a3b8);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  GLASS PANEL                                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

QFrame#glassPanel {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
}

QFrame#glassPanel:hover {
    border-color: rgba(255, 255, 255, 0.15);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  MODULE CARD                                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

QFrame#moduleCard {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
}

QFrame#moduleCard:hover {
    background: rgba(30, 41, 59, 0.8);
    border-color: rgba(255, 255, 255, 0.15);
}

QFrame#moduleCard[active="true"] {
    border: 1px solid rgba(59, 130, 246, 0.5);
    background: rgba(30, 41, 59, 0.9);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  RANGE SLIDERS                                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

QSlider::groove:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #334155, stop: 1 #475569);
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 50%;
    border: 2px solid rgba(59, 130, 246, 0.5);
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #60a5fa, stop: 1 #a78bfa);
    border: 2px solid rgba(96, 165, 250, 0.8);
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    border-radius: 2px;
}

QSlider::add-page:horizontal {
    background: transparent;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  PUSH BUTTONS                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

QPushButton#primaryBtn {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: white;
    font-weight: 600;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #60a5fa, stop: 1 #a78bfa);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #2563eb, stop: 0 #7c3aed);
}

QPushButton#transportBtn {
    background: #1e293b;
    border: 2px solid #334155;
    border-radius: 24px;
    width: 48px;
    height: 48px;
    color: #94a3b8;
    font-size: 18px;
}

QPushButton#transportBtn:hover {
    background: #334155;
    border-color: #475569;
    color: white;
}

QPushButton#transportBtn[active="true"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    border-color: rgba(59, 130, 246, 0.5);
    color: white;
}

QPushButton#tabBtn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 20px;
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#tabBtn:hover {
    color: #e2e8f0;
    background: rgba(59, 130, 246, 0.1);
}

QPushButton#tabBtn[active="true"] {
    color: #3b82f6;
    background: rgba(59, 130, 246, 0.1);
    border-bottom: 2px solid #3b82f6;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TOGGLE SWITCH                                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

QCheckBox#toggleSwitch {
    spacing: 0;
}

QCheckBox#toggleSwitch::indicator {
    width: 44px;
    height: 22px;
    border-radius: 11px;
    background-color: #334155;
    border: none;
}

QCheckBox#toggleSwitch::indicator:hover {
    background-color: #475569;
}

QCheckBox#toggleSwitch::indicator:checked {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  INPUTS                                                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e2e8f0;
    font-size: 12px;
}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #475569;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #94a3b8;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #e2e8f0;
    selection-background-color: rgba(59, 130, 246, 0.3);
}

QComboBox QAbstractItemView::item {
    padding: 8px;
}

QComboBox QAbstractItemView::item:selected {
    background: rgba(59, 130, 246, 0.3);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TABS                                                                        */
/* ═══════════════════════════════════════════════════════════════════════════ */

QPushButton#tabBtn {
    position: relative;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  LABELS                                                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

QLabel#headerLabel {
    color: #3b82f6;
    font-size: 18px;
    font-weight: bold;
    padding: 10px;
}

QLabel#sectionLabel {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

QLabel#timeDisplay {
    color: #3b82f6;
    font-family: 'Courier New', 'Consolas', monospace;
    font-size: 22px;
    letter-spacing: 3px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #0f172a, stop: 1 #1e293b);
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px 20px;
    min-width: 140px;
}

QLabel#moduleTitle {
    color: white;
    font-weight: 600;
    font-size: 13px;
}

QLabel#moduleValue {
    color: #3b82f6;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  PROGRESS BAR                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

QProgressBar {
    background: #1e293b;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: white;
    font-size: 11px;
    font-weight: 600;
    min-height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    border-radius: 6px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  WAVEFORM FRAME                                                              */
/* ═══════════════════════════════════════════════════════════════════════════ */

QFrame#waveformFrame {
    background: #0f172a;
    border: 2px solid #1e293b;
    border-radius: 10px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  HEADER FRAME                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

QFrame#headerFrame {
    background: rgba(30, 41, 59, 0.6);
    border-bottom: 1px solid rgba(51, 65, 119, 0.5);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  SIDE PANELS                                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

QFrame#leftPanel {
    background: rgba(30, 41, 59, 0.3);
    border-right: 1px solid rgba(51, 65, 119, 0.5);
}

QFrame#rightPanel {
    background: rgba(30, 41, 59, 0.3);
    border-left: 1px solid rgba(51, 65, 119, 0.5);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CHECKBOXES                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */

QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
    font-size: 11px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    background: #1e293b;
    border: 1px solid #334155;
}

QCheckBox::indicator:hover {
    border-color: #475569;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #3b82f6, stop: 1 #8b5cf6);
    border-color: #3b82f6;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  GROUP BOX                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */

QGroupBox {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(51, 65, 119, 0.5);
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
    font-size: 11px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 2px;
    padding: 0 8px;
    color: #3b82f6;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  STATUS BAR                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */

QStatusBar {
    background: rgba(15, 23, 42, 0.8);
    border-top: 1px solid rgba(51, 65, 119, 0.5);
    color: #94a3b8;
    font-size: 11px;
}

QStatusBar QLabel {
    color: #94a3b8;
    font-size: 11px;
    padding: 4px 8px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TOOL TIPS                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */

QToolTip {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e2e8f0;
    font-size: 11px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  SPLITTER                                                                    */
/* ═══════════════════════════════════════════════════════════════════════════ */

QSplitter::handle {
    background: rgba(51, 65, 119, 0.5);
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

QSplitter::handle:hover {
    background: rgba(59, 130, 246, 0.5);
}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE CARD
# ══════════════════════════════════════════════════════════════════════════════

class ModuleCard(QFrame):
    """Карточка модуля с полной стилизацией как в HTML."""
    
    value_changed = pyqtSignal(str, object)
    
    def __init__(self, name, color, parent=None):
        super().__init__(parent)
        self.setObjectName('moduleCard')
        self.setProperty('active', False)
        self.setFixedHeight(130)
        
        self.name = name
        self.color = QColor(color)
        self.enabled = False
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        # Color dot + name
        dot_row = QHBoxLayout()
        dot = QLabel('●')
        dot.setStyleSheet(f"color: {self.color.name()}; font-size: 10px;")
        dot_row.addWidget(dot)
        
        name_label = QLabel(self.name)
        name_label.setObjectName('moduleTitle')
        dot_row.addWidget(name_label)
        dot_row.addStretch()
        
        header.addLayout(dot_row)
        
        # Toggle switch
        self.toggle = QCheckBox()
        self.toggle.setObjectName('toggleSwitch')
        self.toggle.toggled.connect(self._on_toggled)
        header.addWidget(self.toggle)
        
        layout.addLayout(header)
        
        # Content
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)
        
    def _on_toggled(self, checked):
        self.enabled = checked
        self.setProperty('active', checked)
        self.style().unpolish(self)
        self.style().polish(self)
        self.value_changed.emit(self.name, checked)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DAW WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class DAWMainWindow(QMainWindow):
    """Главное окно в стиле DAW — ПОЛНАЯ копия asdas.html."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VK Track Modifier — DAW Edition")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        self._init_ui()
        self.setStyleSheet(DAW_STYLESHEET)
        
    def _init_ui(self):
        """Создать интерфейс."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self._build_header(main_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        
        # Left panel
        self._build_left_panel(content_layout)
        
        # Center panel
        self._build_center_panel(content_layout)
        
        # Right panel
        self._build_right_panel(content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Status bar
        self._setup_status_bar()
        
    def _build_header(self, parent):
        """Верхняя панель."""
        header = QFrame()
        header.setObjectName('headerFrame')
        header.setFixedHeight(64)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Logo + Title
        logo_row = QHBoxLayout()
        
        logo_icon = QFrame()
        logo_icon.setFixedSize(40, 40)
        logo_icon.setStyleSheet(f"""
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #3b82f6, stop: 1 #8b5cf6);
            border-radius: 10px;
        """)
        logo_row.addWidget(logo_icon)
        
        title_layout = QVBoxLayout()
        title = QLabel("VK Modifier")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("DAW EDITION")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 9px; letter-spacing: 2px;")
        title_layout.addWidget(subtitle)
        
        logo_row.addLayout(title_layout)
        logo_row.addSpacing(20)
        
        layout.addLayout(logo_row)
        
        # Time display
        self.time_display = QLabel("00:00:00")
        self.time_display.setObjectName('timeDisplay')
        layout.addWidget(self.time_display)
        
        layout.addStretch()
        
        # Transport controls
        transport_row = QHBoxLayout()
        transport_row.setSpacing(8)
        
        self.btn_begin = QPushButton("⏮")
        self.btn_begin.setObjectName('transportBtn')
        self.btn_begin.setFixedSize(48, 48)
        transport_row.addWidget(self.btn_begin)
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setObjectName('transportBtn')
        self.btn_play.setProperty('active', True)
        self.btn_play.setFixedSize(48, 48)
        transport_row.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setObjectName('transportBtn')
        self.btn_stop.setFixedSize(48, 48)
        transport_row.addWidget(self.btn_stop)
        
        self.btn_record = QPushButton("●")
        self.btn_record.setObjectName('transportBtn')
        self.btn_record.setFixedSize(48, 48)
        self.btn_record.setStyleSheet("color: #ef4444;")
        transport_row.addWidget(self.btn_record)
        
        layout.addLayout(transport_row)
        
        layout.addStretch()
        
        # Export button
        self.btn_export = QPushButton("⚡ Экспорт")
        self.btn_export.setObjectName('primaryBtn')
        self.btn_export.setFixedHeight(40)
        layout.addWidget(self.btn_export)
        
        parent.addWidget(header)
        
    def _build_left_panel(self, parent):
        """Левая панель — Channel Rack."""
        left_panel = QFrame()
        left_panel.setObjectName('leftPanel')
        left_panel.setFixedWidth(290)
        
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("border-bottom: 1px solid rgba(51, 65, 119, 0.5);")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title = QLabel("МОДУЛИ ОБРАБОТКИ")
        title.setObjectName('sectionLabel')
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        reset_btn = QPushButton("🔄")
        reset_btn.setStyleSheet("""
            background: transparent;
            border: none;
            color: #64748b;
            font-size: 14px;
        """)
        header_layout.addWidget(reset_btn)
        
        layout.addWidget(header)
        
        # Modules scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        modules_widget = QWidget()
        modules_layout = QVBoxLayout(modules_widget)
        modules_layout.setContentsMargins(10, 10, 10, 10)
        modules_layout.setSpacing(10)
        
        # Pitch Module
        pitch_module = ModuleCard("Pitch", "#3b82f6")
        pitch_module.setProperty('active', True)
        
        pitch_slider = QSlider(Qt.Horizontal)
        pitch_slider.setRange(-240, 240)
        pitch_slider.setValue(0)
        pitch_slider.valueChanged.connect(lambda v: pitch_value.setText(f"{v/10:.1f}"))
        
        pitch_row = QHBoxLayout()
        pitch_min = QLabel("-24")
        pitch_min.setStyleSheet("color: #64748b; font-size: 10px;")
        pitch_row.addWidget(pitch_min)
        
        pitch_row.addWidget(pitch_slider, 1)
        
        pitch_max = QLabel("+24")
        pitch_max.setStyleSheet("color: #64748b; font-size: 10px;")
        pitch_row.addWidget(pitch_max)
        
        pitch_value = QLabel("0.0")
        pitch_value.setObjectName('moduleValue')
        pitch_value.setFixedWidth(50)
        pitch_value.setAlignment(Qt.AlignRight)
        pitch_row.addWidget(pitch_value)
        
        pitch_module.content_layout.addLayout(pitch_row)
        modules_layout.addWidget(pitch_module)
        
        # Speed Module
        speed_module = ModuleCard("Speed", "#10b981")
        
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(95, 105)
        speed_slider.setValue(100)
        speed_slider.valueChanged.connect(lambda v: speed_value.setText(f"{v/100:.2f}x"))
        
        speed_row = QHBoxLayout()
        speed_min = QLabel("0.95x")
        speed_min.setStyleSheet("color: #64748b; font-size: 10px;")
        speed_row.addWidget(speed_min)
        
        speed_row.addWidget(speed_slider, 1)
        
        speed_max = QLabel("1.05x")
        speed_max.setStyleSheet("color: #64748b; font-size: 10px;")
        speed_row.addWidget(speed_max)
        
        speed_value = QLabel("1.00x")
        speed_value.setObjectName('moduleValue')
        speed_value.setFixedWidth(50)
        speed_value.setAlignment(Qt.AlignRight)
        speed_row.addWidget(speed_value)
        
        speed_module.content_layout.addLayout(speed_row)
        modules_layout.addWidget(speed_module)
        
        # EQ Module
        eq_module = ModuleCard("EQ", "#8b5cf6")
        
        eq_combo = QComboBox()
        eq_combo.addItems([
            "Нет коррекции",
            "Лёгкая (-2dB @ 1kHz)",
            "Средняя (-4dB @ 1kHz)",
            "Сильная (-6dB @ 1kHz)",
            "Boost середины",
            "Boost верхов"
        ])
        eq_module.content_layout.addWidget(eq_combo)
        modules_layout.addWidget(eq_module)
        
        # Phase Module
        phase_module = ModuleCard("Phase", "#ec4899")
        
        phase_input = QHBoxLayout()
        phase_spin = QDoubleSpinBox()
        phase_spin.setRange(0, 10)
        phase_spin.setValue(0)
        phase_spin.setSuffix(" ms")
        phase_spin.setDecimals(1)
        phase_input.addWidget(phase_spin)
        
        phase_module.content_layout.addLayout(phase_input)
        modules_layout.addWidget(phase_module)
        
        # Compression Module
        comp_module = ModuleCard("Compress", "#f59e0b")
        
        comp_row = QHBoxLayout()
        comp_row.setSpacing(4)
        
        attack_lbl = QLabel("Attack: 0.1s")
        attack_lbl.setStyleSheet("""
            background: #1e293b;
            color: #94a3b8;
            font-size: 9px;
            padding: 6px 8px;
            border-radius: 4px;
        """)
        comp_row.addWidget(attack_lbl, 1)
        
        decay_lbl = QLabel("Decay: 0.1s")
        decay_lbl.setStyleSheet("""
            background: #1e293b;
            color: #94a3b8;
            font-size: 9px;
            padding: 6px 8px;
            border-radius: 4px;
        """)
        comp_row.addWidget(decay_lbl, 1)
        
        comp_module.content_layout.addLayout(comp_row)
        modules_layout.addWidget(comp_module)
        
        # FX Chain Module
        fx_module = ModuleCard("FX Chain", "#06b6d4")
        
        fx_noise = QCheckBox("Pink Noise")
        fx_noise.setStyleSheet("color: #94a3b8; font-size: 10px;")
        fx_module.content_layout.addWidget(fx_noise)
        
        fx_ultra = QCheckBox("Ultrasound")
        fx_ultra.setStyleSheet("color: #94a3b8; font-size: 10px;")
        fx_module.content_layout.addWidget(fx_ultra)
        
        fx_dc = QCheckBox("DC Shift")
        fx_dc.setStyleSheet("color: #94a3b8; font-size: 10px;")
        fx_module.content_layout.addWidget(fx_dc)
        
        modules_layout.addWidget(fx_module)
        
        # Fade Module
        fade_module = ModuleCard("Fade", "#f97316")
        
        fade_row = QHBoxLayout()
        fade_row.setSpacing(10)
        
        fade_in_col = QVBoxLayout()
        fade_in_lbl = QLabel("In")
        fade_in_lbl.setStyleSheet("color: #64748b; font-size: 9px;")
        fade_in_col.addWidget(fade_in_lbl)
        
        fade_in_spin = QDoubleSpinBox()
        fade_in_spin.setRange(0, 10)
        fade_in_spin.setValue(0)
        fade_in_spin.setSuffix("s")
        fade_in_col.addWidget(fade_in_spin)
        
        fade_row.addLayout(fade_in_col)
        
        fade_out_col = QVBoxLayout()
        fade_out_lbl = QLabel("Out")
        fade_out_lbl.setStyleSheet("color: #64748b; font-size: 9px;")
        fade_out_col.addWidget(fade_out_lbl)
        
        fade_out_spin = QDoubleSpinBox()
        fade_out_spin.setRange(0, 10)
        fade_out_spin.setValue(0)
        fade_out_spin.setSuffix("s")
        fade_out_col.addWidget(fade_out_spin)
        
        fade_row.addLayout(fade_out_col)
        
        fade_module.content_layout.addLayout(fade_row)
        modules_layout.addWidget(fade_module)
        
        modules_layout.addStretch()
        
        scroll.setWidget(modules_widget)
        layout.addWidget(scroll)
        
        # Add module button
        add_btn = QPushButton("➕ Добавить модуль")
        add_btn.setStyleSheet("""
            background: #1e293b;
            border: 1px dashed #475569;
            border-radius: 8px;
            padding: 12px;
            color: #94a3b8;
            font-size: 12px;
        """)
        add_btn.setFixedHeight(44)
        layout.addWidget(add_btn)
        
        parent.addWidget(left_panel)
        
    def _build_center_panel(self, parent):
        """Центральная панель."""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        # Waveform area
        waveform_frame = QFrame()
        waveform_frame.setObjectName('waveformFrame')
        waveform_frame.setMinimumHeight(300)
        
        waveform_layout = QVBoxLayout(waveform_frame)
        waveform_layout.setContentsMargins(20, 20, 20, 20)
        
        placeholder = QLabel("🎵 Перетащите аудиофайл или нажмите кнопку ниже")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #94a3b8;
            font-size: 16px;
            background: transparent;
        """)
        waveform_layout.addWidget(placeholder)
        
        center_layout.addWidget(waveform_frame, 1)
        
        # Structure panel
        structure_panel = QFrame()
        structure_panel.setObjectName('glassPanel')
        structure_panel.setFixedHeight(180)
        
        sp_layout = QHBoxLayout(structure_panel)
        sp_layout.setContentsMargins(20, 15, 20, 15)
        sp_layout.setSpacing(30)
        
        # Cut controls
        cut_group = QVBoxLayout()
        
        cut_header = QHBoxLayout()
        cut_icon = QLabel("✂️")
        cut_header.addWidget(cut_icon)
        
        cut_title = QLabel("ОБРЕЗКА / ВЫРЕЗКА")
        cut_title.setObjectName('sectionLabel')
        cut_title.setStyleSheet("color: #f59e0b;")
        cut_header.addWidget(cut_title)
        cut_header.addStretch()
        
        cut_group.addLayout(cut_header)
        
        # Sliders
        trim_layout = QHBoxLayout()
        trim_label = QLabel("Trim Start:")
        trim_label.setStyleSheet("color: #64748b; font-size: 10px;")
        trim_layout.addWidget(trim_label)
        
        trim_slider = QSlider(Qt.Horizontal)
        trim_slider.setRange(0, 100)
        trim_layout.addWidget(trim_slider)
        
        trim_value = QLabel("0.0s")
        trim_value.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 11px;")
        trim_value.setFixedWidth(50)
        trim_layout.addWidget(trim_value)
        
        cut_group.addLayout(trim_layout)
        
        cut_from_layout = QHBoxLayout()
        cut_from_label = QLabel("Cut From:")
        cut_from_label.setStyleSheet("color: #64748b; font-size: 10px;")
        cut_from_layout.addWidget(cut_from_label)
        
        cut_from_slider = QSlider(Qt.Horizontal)
        cut_from_slider.setRange(0, 100)
        cut_from_slider.setValue(30)
        cut_from_layout.addWidget(cut_from_slider)
        
        cut_from_value = QLabel("0.0s")
        cut_from_value.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 11px;")
        cut_from_value.setFixedWidth(50)
        cut_from_layout.addWidget(cut_from_value)
        
        cut_group.addLayout(cut_from_layout)
        
        cut_to_layout = QHBoxLayout()
        cut_to_label = QLabel("Cut To:")
        cut_to_label.setStyleSheet("color: #64748b; font-size: 10px;")
        cut_to_layout.addWidget(cut_to_label)
        
        cut_to_slider = QSlider(Qt.Horizontal)
        cut_to_slider.setRange(0, 100)
        cut_to_slider.setValue(70)
        cut_to_layout.addWidget(cut_to_slider)
        
        cut_to_value = QLabel("0.0s")
        cut_to_value.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 11px;")
        cut_to_value.setFixedWidth(50)
        cut_to_layout.addWidget(cut_to_value)
        
        cut_group.addLayout(cut_to_layout)
        
        silence_layout = QHBoxLayout()
        silence_label = QLabel("Silence End:")
        silence_label.setStyleSheet("color: #64748b; font-size: 10px;")
        silence_layout.addWidget(silence_label)
        
        silence_slider = QSlider(Qt.Horizontal)
        silence_slider.setRange(0, 30)
        silence_layout.addWidget(silence_slider)
        
        silence_value = QLabel("0.0s")
        silence_value.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 11px;")
        silence_value.setFixedWidth(50)
        silence_layout.addWidget(silence_value)
        
        cut_group.addLayout(silence_layout)
        
        sp_layout.addLayout(cut_group, 1)
        
        # Divider
        divider = QFrame()
        divider.setFixedWidth(2)
        divider.setStyleSheet("background: #334155;")
        sp_layout.addWidget(divider)
        
        # Merge controls
        merge_group = QVBoxLayout()
        
        merge_header = QHBoxLayout()
        merge_icon = QLabel("🔗")
        merge_header.addWidget(merge_icon)
        
        merge_title = QLabel("СРАЩИВАНИЕ")
        merge_title.setObjectName('sectionLabel')
        merge_title.setStyleSheet("color: #10b981;")
        merge_header.addWidget(merge_title)
        merge_header.addStretch()
        
        merge_group.addLayout(merge_header)
        
        merge_check = QCheckBox("Включить Merge")
        merge_check.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        merge_group.addWidget(merge_check)
        
        merge_btn = QPushButton("➕ Добавить трек")
        merge_btn.setStyleSheet("""
            background: #1e293b;
            border: none;
            border-radius: 6px;
            padding: 8px;
            color: #94a3b8;
            font-size: 11px;
        """)
        merge_btn.setFixedHeight(36)
        merge_group.addWidget(merge_btn)
        
        merge_info = QLabel("🎵 track_002.mp3")
        merge_info.setStyleSheet("""
            background: rgba(30, 41, 59, 0.5);
            border-radius: 6px;
            padding: 8px;
            color: #94a3b8;
            font-size: 10px;
        """)
        merge_info.setVisible(False)
        merge_group.addWidget(merge_info)
        
        merge_group.addStretch()
        
        sp_layout.addLayout(merge_group)
        
        center_layout.addWidget(structure_panel)
        
        parent.addWidget(center_widget)
        
    def _build_right_panel(self, parent):
        """Правая панель."""
        right_panel = QFrame()
        right_panel.setObjectName('rightPanel')
        right_panel.setFixedWidth(320)
        
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tabs
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(0)
        
        self.tab_metadata = QPushButton("🏷️ Теги")
        self.tab_metadata.setObjectName('tabBtn')
        self.tab_metadata.setProperty('active', True)
        self.tab_metadata.setFixedHeight(48)
        tabs_row.addWidget(self.tab_metadata)
        
        self.tab_encoding = QPushButton("💾 Код")
        self.tab_encoding.setObjectName('tabBtn')
        self.tab_encoding.setFixedHeight(48)
        tabs_row.addWidget(self.tab_encoding)
        
        self.tab_antidetect = QPushButton("🎭 Anti")
        self.tab_antidetect.setObjectName('tabBtn')
        self.tab_antidetect.setFixedHeight(48)
        tabs_row.addWidget(self.tab_antidetect)
        
        layout.addLayout(tabs_row)
        
        # Tab content
        tab_content = QScrollArea()
        tab_content.setWidgetResizable(True)
        tab_content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(18)
        
        # Cover art
        cover_frame = QFrame()
        cover_frame.setObjectName('glassPanel')
        cover_layout = QVBoxLayout(cover_frame)
        cover_layout.setContentsMargins(15, 15, 15, 15)
        cover_layout.setAlignment(Qt.AlignCenter)
        
        cover_placeholder = QLabel("🖼️")
        cover_placeholder.setStyleSheet("""
            background: rgba(59, 130, 246, 0.1);
            border: 2px dashed #475569;
            border-radius: 8px;
            color: #64748b;
            font-size: 48px;
        """)
        cover_placeholder.setFixedSize(128, 128)
        cover_placeholder.setAlignment(Qt.AlignCenter)
        cover_layout.addWidget(cover_placeholder)
        
        cover_row = QHBoxLayout()
        cover_row.setSpacing(4)
        
        btn_original = QPushButton("Оригинал")
        btn_original.setStyleSheet("""
            background: #1e293b;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            color: #94a3b8;
            font-size: 10px;
        """)
        cover_row.addWidget(btn_original)
        
        btn_random = QPushButton("Случайная")
        btn_random.setStyleSheet("""
            background: #1e293b;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            color: #94a3b8;
            font-size: 10px;
        """)
        cover_row.addWidget(btn_random)
        
        btn_remove = QPushButton("🗑️")
        btn_remove.setStyleSheet("""
            background: #1e293b;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            color: #ef4444;
            font-size: 10px;
        """)
        cover_row.addWidget(btn_remove)
        
        cover_layout.addLayout(cover_row)
        content_layout.addWidget(cover_frame)
        
        # Tag fields
        title_lbl = QLabel("TITLE")
        title_lbl.setStyleSheet("color: #64748b; font-size: 9px; letter-spacing: 1px;")
        content_layout.addWidget(title_lbl)
        
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Song Title")
        content_layout.addWidget(title_edit)
        
        artist_lbl = QLabel("ARTIST")
        artist_lbl.setStyleSheet("color: #64748b; font-size: 9px; letter-spacing: 1px;")
        content_layout.addWidget(artist_lbl)
        
        artist_edit = QLineEdit()
        artist_edit.setPlaceholderText("Artist")
        content_layout.addWidget(artist_edit)
        
        album_year_row = QHBoxLayout()
        album_year_row.setSpacing(8)
        
        album_col = QVBoxLayout()
        album_lbl = QLabel("ALBUM")
        album_lbl.setStyleSheet("color: #64748b; font-size: 9px; letter-spacing: 1px;")
        album_col.addWidget(album_lbl)
        
        album_edit = QLineEdit()
        album_col.addWidget(album_edit)
        
        album_year_row.addLayout(album_col)
        
        year_col = QVBoxLayout()
        year_lbl = QLabel("YEAR")
        year_lbl.setStyleSheet("color: #64748b; font-size: 9px; letter-spacing: 1px;")
        year_col.addWidget(year_lbl)
        
        year_edit = QLineEdit()
        year_edit.setPlaceholderText("2024")
        year_col.addWidget(year_edit)
        
        album_year_row.addLayout(year_col)
        
        content_layout.addLayout(album_year_row)
        
        genre_lbl = QLabel("GENRE")
        genre_lbl.setStyleSheet("color: #64748b; font-size: 9px; letter-spacing: 1px;")
        content_layout.addWidget(genre_lbl)
        
        genre_combo = QComboBox()
        genre_combo.addItems(["Выбрать жанр", "Pop", "Rock", "Electronic", "Hip-Hop", "R&B", "Jazz", "Classical", "Other"])
        content_layout.addWidget(genre_combo)
        
        content_layout.addStretch()
        
        tab_content.setWidget(content_widget)
        layout.addWidget(tab_content)
        
        # Start button
        self.btn_start = QPushButton("🚀 ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setObjectName('primaryBtn')
        self.btn_start.setFixedHeight(60)
        self.btn_start.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self.btn_start)
        
        parent.addWidget(right_panel)
        
    def _setup_status_bar(self):
        """Статус бар."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_files = QLabel("0 файлов")
        self.status_version = QLabel("v2.1.0")
        
        self.status_bar.addWidget(self.status_files)
        self.status_bar.addPermanentWidget(self.status_version)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)
    
    window = DAWMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
