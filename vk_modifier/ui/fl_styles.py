"""FL Studio-inspired стили для vk_modifier."""

# ══════════════════════════════════════════════════════════════════════════════
#  ЦВЕТОВАЯ ПАЛИТРА
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Основные цвета
    'bg_dark': '#1a1a2e',
    'bg_main': '#16213e',
    'bg_panel': '#0f3460',
    'bg_light': '#1a1a2e',
    
    # Акцентные цвета
    'accent_primary': '#e94560',
    'accent_secondary': '#00adb5',
    'accent_success': '#00ff88',
    'accent_warning': '#ffaa00',
    'accent_danger': '#ff4757',
    
    # Текст
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0a0',
    'text_muted': '#606060',
    
    # Границы
    'border_dark': '#2a2a3e',
    'border_light': '#3a3a5e',
    
    # Градиенты
    'gradient_start': '#e94560',
    'gradient_end': '#ff6b6b',
}


def get_stylesheet() -> str:
    """Генерация полной таблицы стилей."""
    c = COLORS
    
    return f"""
/* ═════════════════════════════════════════════════════════════════════════════ */
/*  GLOBAL STYLES                                                                */
/* ═════════════════════════════════════════════════════════════════════════════ */

* {{
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    outline: none;
}}

QMainWindow {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['bg_dark']},
        stop: 0.5 {c['bg_main']},
        stop: 1 {c['bg_light']}
    );
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  SCROLLBARS                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QScrollBar:vertical {{
    background: {c['bg_dark']};
    width: 10px;
    border-left: 1px solid {c['border_dark']};
}}

QScrollBar::handle:vertical {{
    background: {c['border_light']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c['accent_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: {c['bg_dark']};
    height: 10px;
    border-top: 1px solid {c['border_dark']};
}}

QScrollBar::handle:horizontal {{
    background: {c['border_light']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  LABELS                                                                       */
/* ═════════════════════════════════════════════════════════════════════════════ */

QLabel {{
    color: {c['text_primary']};
    font-size: 13px;
    background: transparent;
}}

QLabel#headerLabel {{
    color: {c['accent_primary']};
    font-size: 16px;
    font-weight: bold;
    padding: 10px;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['bg_dark']},
        stop: 1 {c['bg_panel']}
    );
    border-radius: 8px;
}}

QLabel#sectionLabel {{
    color: {c['accent_secondary']};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 5px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  LINE EDITS                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QLineEdit {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {c['text_primary']};
    font-size: 13px;
    selection-background-color: {c['accent_secondary']};
}}

QLineEdit:hover {{
    border-color: {c['border_light']};
}}

QLineEdit:focus {{
    border-color: {c['accent_secondary']};
    background: {c['bg_main']};
}}

QLineEdit:disabled {{
    background: {c['bg_panel']};
    color: {c['text_muted']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  CHECKBOXES                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QCheckBox {{
    spacing: 10px;
    color: {c['text_primary']};
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 5px;
    background: {c['bg_dark']};
    border: 2px solid {c['border_light']};
}}

QCheckBox::indicator:hover {{
    border-color: {c['accent_secondary']};
}}

QCheckBox::indicator:checked {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    border-color: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  COMBOBOXES                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QComboBox {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {c['text_primary']};
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {c['border_light']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 7px solid {c['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background: {c['bg_main']};
    border: 2px solid {c['border_dark']};
    border-radius: 6px;
    selection-background-color: {c['accent_secondary']};
    color: {c['text_primary']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px;
    border-radius: 4px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  SLIDERS                                                                      */
/* ═════════════════════════════════════════════════════════════════════════════ */

QSlider::groove:horizontal {{
    background: {c['bg_dark']};
    height: 8px;
    border-radius: 4px;
    border: 1px solid {c['border_dark']};
}}

QSlider::handle:horizontal {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    width: 18px;
    height: 24px;
    margin: -9px 0;
    border-radius: 4px;
    border: 2px solid {c['border_light']};
}}

QSlider::handle:horizontal:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #00ffff,
        stop: 1 {c['accent_secondary']}
    );
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    border-radius: 4px;
}}

QSlider::groove:vertical {{
    background: {c['bg_dark']};
    width: 8px;
    border-radius: 4px;
    border: 1px solid {c['border_dark']};
}}

QSlider::handle:vertical {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    width: 24px;
    height: 18px;
    margin: 0 -9px;
    border-radius: 4px;
    border: 2px solid {c['border_light']};
}}

QSlider::sub-page:vertical {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    border-radius: 4px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  SPINBOXES                                                                    */
/* ═════════════════════════════════════════════════════════════════════════════ */

QSpinBox, QDoubleSpinBox {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {c['text_primary']};
    font-size: 13px;
    min-height: 20px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {c['border_light']};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {c['bg_panel']};
    border: none;
    width: 20px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  LIST WIDGETS                                                                 */
/* ═════════════════════════════════════════════════════════════════════════════ */

QListWidget {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
    padding: 6px;
    outline: none;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 6px;
    margin: 3px 0;
    color: {c['text_primary']};
    border: none;
}}

QListWidget::item:selected {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['bg_panel']},
        stop: 1 {c['accent_secondary']}
    );
    border-left: 4px solid {c['accent_secondary']};
}}

QListWidget::item:hover {{
    background: {c['bg_panel']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  TEXT EDITS                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QTextEdit {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
    padding: 10px;
    color: {c['text_secondary']};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}}

QTextEdit:focus {{
    border-color: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  PROGRESS BARS                                                                */
/* ═════════════════════════════════════════════════════════════════════════════ */

QProgressBar {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
    text-align: center;
    color: {c['text_primary']};
    font-size: 12px;
    font-weight: 600;
    min-height: 24px;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['accent_secondary']},
        stop: 0.5 {c['accent_primary']},
        stop: 1 {c['gradient_end']}
    );
    border-radius: 7px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  GROUP BOXES                                                                  */
/* ═════════════════════════════════════════════════════════════════════════════ */

QGroupBox {{
    background: {c['bg_panel']};
    border: 2px solid {c['border_dark']};
    border-radius: 10px;
    margin-top: 20px;
    padding-top: 20px;
    font-size: 12px;
    font-weight: bold;
    color: {c['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 15px;
    top: 2px;
    padding: 0 10px;
    color: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  TABS                                                                         */
/* ═════════════════════════════════════════════════════════════════════════════ */

QTabWidget::pane {{
    background: {c['bg_panel']};
    border: 2px solid {c['border_dark']};
    border-radius: 10px;
    padding: 10px;
}}

QTabBar::tab {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 25px;
    margin-right: 4px;
    color: {c['text_secondary']};
    font-size: 13px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: {c['bg_panel']};
    border-color: {c['border_light']};
    color: {c['text_primary']};
}}

QTabBar::tab:hover:!selected {{
    background: {c['bg_main']};
    color: {c['text_primary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  PUSH BUTTONS                                                                 */
/* ═════════════════════════════════════════════════════════════════════════════ */

QPushButton {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['bg_panel']},
        stop: 1 {c['bg_dark']}
    );
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
    padding: 10px 20px;
    color: {c['text_primary']};
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['border_light']},
        stop: 1 {c['bg_panel']}
    );
    border-color: {c['accent_secondary']};
}}

QPushButton:pressed {{
    background: {c['bg_dark']};
}}

QPushButton:disabled {{
    background: {c['bg_panel']};
    color: {c['text_muted']};
    border-color: {c['border_dark']};
}}

/* Special Buttons */
QPushButton#primaryBtn {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_primary']},
        stop: 1 {c['gradient_end']}
    );
    border: 2px solid {c['accent_primary']};
    color: {c['text_primary']};
}}

QPushButton#primaryBtn:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ff6b6b,
        stop: 1 {c['accent_primary']}
    );
}}

QPushButton#secondaryBtn {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_secondary']},
        stop: 1 #00ffff
    );
    border: 2px solid {c['accent_secondary']};
    color: {c['bg_dark']};
    font-weight: bold;
}}

QPushButton#secondaryBtn:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #00ffff,
        stop: 1 {c['accent_secondary']}
    );
}}

QPushButton#dangerBtn {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_danger']},
        stop: 1 #ff6b6b
    );
    border: 2px solid {c['accent_danger']};
    color: {c['text_primary']};
}}

QPushButton#dangerBtn:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ff6b6b,
        stop: 1 {c['accent_danger']}
    );
}}

QPushButton#successBtn {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['accent_success']},
        stop: 1 #00ffaa
    );
    border: 2px solid {c['accent_success']};
    color: {c['bg_dark']};
    font-weight: bold;
}}

QPushButton#successBtn:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #00ffaa,
        stop: 1 {c['accent_success']}
    );
}}

/* Transport Buttons */
QPushButton#transportBtn {{
    background: {c['bg_dark']};
    border: 3px solid {c['border_light']};
    border-radius: 25px;
    width: 50px;
    height: 50px;
    color: {c['text_secondary']};
    font-size: 20px;
}}

QPushButton#transportBtn:hover {{
    border-color: {c['accent_secondary']};
    color: {c['accent_secondary']};
    background: {c['bg_panel']};
}}

QPushButton#transportBtn:checked {{
    background: {c['accent_success']};
    color: {c['bg_dark']};
    border-color: {c['accent_success']};
}}

QPushButton#transportBtn:disabled {{
    background: {c['bg_dark']};
    color: {c['text_muted']};
    border-color: {c['border_dark']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  TOOL TIPS                                                                    */
/* ═════════════════════════════════════════════════════════════════════════════ */

QToolTip {{
    background: {c['bg_main']};
    border: 2px solid {c['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {c['text_primary']};
    font-size: 12px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  MENUS                                                                        */
/* ═════════════════════════════════════════════════════════════════════════════ */

QMenu {{
    background: {c['bg_main']};
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
    padding: 6px;
}}

QMenu::item {{
    padding: 10px 25px 10px 15px;
    border-radius: 4px;
    color: {c['text_primary']};
}}

QMenu::item:selected {{
    background: {c['bg_panel']};
}}

QMenu::separator {{
    height: 2px;
    background: {c['border_dark']};
    margin: 6px 8px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  STATUS BAR                                                                   */
/* ═════════════════════════════════════════════════════════════════════════════ */

QStatusBar {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 {c['bg_dark']},
        stop: 1 {c['bg_main']}
    );
    border-top: 2px solid {c['border_dark']};
    color: {c['text_secondary']};
    font-size: 12px;
}}

QStatusBar QLabel {{
    color: {c['text_secondary']};
    font-size: 12px;
    padding: 4px 10px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  SPLITTER                                                                     */
/* ═════════════════════════════════════════════════════════════════════════════ */

QSplitter::handle {{
    background: {c['border_dark']};
}}

QSplitter::handle:horizontal {{
    width: 6px;
}}

QSplitter::handle:vertical {{
    height: 6px;
}}

QSplitter::handle:hover {{
    background: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  FRAMES & PANELS                                                              */
/* ═════════════════════════════════════════════════════════════════════════════ */

QFrame#cardFrame {{
    background: {c['bg_panel']};
    border: 2px solid {c['border_dark']};
    border-radius: 12px;
    padding: 15px;
}}

QFrame#cardFrame:hover {{
    border-color: {c['border_light']};
}}

QFrame#headerFrame {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {c['bg_dark']},
        stop: 0.5 {c['bg_main']},
        stop: 1 {c['bg_dark']}
    );
    border-bottom: 2px solid {c['border_dark']};
}}

QFrame#panelFrame {{
    background: {c['bg_main']};
    border: 2px solid {c['border_dark']};
    border-radius: 10px;
}}

QFrame#waveformFrame {{
    background: {c['bg_dark']};
    border: 2px solid {c['border_dark']};
    border-radius: 10px;
}}

QFrame#mixerFrame {{
    background: {c['bg_panel']};
    border: 2px solid {c['border_dark']};
    border-radius: 8px;
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  RADIO BUTTONS                                                                */
/* ═════════════════════════════════════════════════════════════════════════════ */

QRadioButton {{
    color: {c['text_primary']};
    font-size: 13px;
    spacing: 10px;
}}

QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 10px;
    background: {c['bg_dark']};
    border: 2px solid {c['border_light']};
}}

QRadioButton::indicator:checked {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 {c['accent_secondary']},
        stop: 1 {c['accent_primary']}
    );
    border-color: {c['accent_secondary']};
}}

/* ═════════════════════════════════════════════════════════════════════════════ */
/*  TOOLBAR                                                                      */
/* ═════════════════════════════════════════════════════════════════════════════ */

QToolBar {{
    background: {c['bg_panel']};
    border: none;
    border-bottom: 2px solid {c['border_dark']};
    padding: 6px;
    spacing: 6px;
}}

QToolBar::separator {{
    width: 3px;
    background: {c['border_dark']};
    margin: 4px 10px;
}}

QToolBar QToolButton {{
    background: transparent;
    border: 2px solid transparent;
    border-radius: 6px;
    padding: 8px 12px;
    color: {c['text_secondary']};
    font-size: 12px;
}}

QToolBar QToolButton:hover {{
    background: {c['bg_dark']};
    border-color: {c['border_light']};
    color: {c['text_primary']};
}}

QToolBar QToolButton:checked {{
    background: {c['accent_secondary']};
    border-color: {c['accent_secondary']};
    color: {c['bg_dark']};
}}
"""


STYLESHEET = get_stylesheet()
