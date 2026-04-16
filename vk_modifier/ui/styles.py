"""Все стили UI в одном месте. Поддержка dark/light тем."""

# ══════════════════════════════════════════════════════════════════════════════
#  ЦВЕТОВЫЕ СХЕМЫ
# ══════════════════════════════════════════════════════════════════════════════

THEMES = {
    'dark': {
        'bg_primary': '#0c0c1e',
        'bg_secondary': '#0f0f24',
        'bg_tertiary': '#0a0a18',
        'surface': 'rgba(255,255,255,0.03)',
        'surface_hover': 'rgba(255,255,255,0.07)',
        'border': 'rgba(255,255,255,0.07)',
        'border_hover': 'rgba(255,255,255,0.18)',
        'text': 'rgba(255,255,255,0.85)',
        'text_dim': 'rgba(255,255,255,0.50)',
        'text_muted': 'rgba(255,255,255,0.30)',
        'text_title': 'rgba(255,255,255,0.92)',
        'input_bg': 'rgba(255,255,255,0.05)',
        'input_border': 'rgba(255,255,255,0.09)',
        'input_focus_border': 'rgba(10,132,255,0.55)',
        'input_focus_bg': 'rgba(255,255,255,0.07)',
        'list_bg': 'rgba(255,255,255,0.025)',
        'list_selected': 'rgba(10,132,255,0.22)',
        'list_hover': 'rgba(255,255,255,0.04)',
        'accent': '#0A84FF',
        'accent_dark': '#0060CC',
        'accent_light': '#5AC8FA',
        'accent_bg': 'rgba(10,132,255,0.35)',
        'danger': 'rgba(255,69,58,0.85)',
        'danger_bg': 'rgba(255,69,58,0.12)',
        'tooltip_bg': '#1c1c36',
        'menu_bg': '#1a1a30',
        'slider_groove': 'rgba(255,255,255,0.08)',
        'slider_sub': 'rgba(10,132,255,0.35)',
        'scrollbar_handle': 'rgba(255,255,255,0.12)',
        'status_bg': 'rgba(255,255,255,0.03)',
        'status_border': 'rgba(255,255,255,0.06)',
        'card_bg': 'rgba(255,255,255,0.03)',
        'card_border': 'rgba(255,255,255,0.07)',
        'check_bg': 'rgba(255,255,255,0.07)',
        'check_border': 'rgba(255,255,255,0.18)',
        'progress_bg': 'rgba(255,255,255,0.05)',
        'progress_border': 'rgba(255,255,255,0.07)',
        'combo_dropdown_bg': '#1a1a30',
    },
    'light': {
        'bg_primary': '#f0f2f5',
        'bg_secondary': '#e8eaed',
        'bg_tertiary': '#f5f6f8',
        'surface': 'rgba(255,255,255,0.85)',
        'surface_hover': 'rgba(255,255,255,0.95)',
        'border': 'rgba(0,0,0,0.10)',
        'border_hover': 'rgba(0,0,0,0.20)',
        'text': 'rgba(0,0,0,0.85)',
        'text_dim': 'rgba(0,0,0,0.50)',
        'text_muted': 'rgba(0,0,0,0.30)',
        'text_title': 'rgba(0,0,0,0.90)',
        'input_bg': 'rgba(255,255,255,0.90)',
        'input_border': 'rgba(0,0,0,0.12)',
        'input_focus_border': 'rgba(10,132,255,0.65)',
        'input_focus_bg': '#ffffff',
        'list_bg': 'rgba(255,255,255,0.80)',
        'list_selected': 'rgba(10,132,255,0.15)',
        'list_hover': 'rgba(0,0,0,0.04)',
        'accent': '#0A84FF',
        'accent_dark': '#0066DD',
        'accent_light': '#40A0FF',
        'accent_bg': 'rgba(10,132,255,0.20)',
        'danger': 'rgba(220,50,40,0.85)',
        'danger_bg': 'rgba(220,50,40,0.08)',
        'tooltip_bg': '#ffffff',
        'menu_bg': '#ffffff',
        'slider_groove': 'rgba(0,0,0,0.10)',
        'slider_sub': 'rgba(10,132,255,0.45)',
        'scrollbar_handle': 'rgba(0,0,0,0.15)',
        'status_bg': 'rgba(0,0,0,0.03)',
        'status_border': 'rgba(0,0,0,0.08)',
        'card_bg': 'rgba(255,255,255,0.80)',
        'card_border': 'rgba(0,0,0,0.08)',
        'check_bg': 'rgba(0,0,0,0.05)',
        'check_border': 'rgba(0,0,0,0.20)',
        'progress_bg': 'rgba(0,0,0,0.06)',
        'progress_border': 'rgba(0,0,0,0.08)',
        'combo_dropdown_bg': '#ffffff',
    },
}


def _gen_stylesheet(t: dict) -> str:
    return f"""
* {{ font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif; }}
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:0.4, y2:1,
        stop:0 {t['bg_primary']}, stop:0.5 {t['bg_secondary']}, stop:1 {t['bg_tertiary']});
}}
QScrollBar:vertical {{ background: transparent; width: 6px; margin: 4px 0; }}
QScrollBar::handle:vertical {{ background: {t['scrollbar_handle']}; border-radius: 3px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {t['border_hover']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; height: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QLabel {{ color: {t['text']}; font-size: 13px; background: transparent; }}
QLineEdit {{
    background: {t['input_bg']}; border: 1px solid {t['input_border']};
    border-radius: 10px; padding: 9px 14px; color: {t['text_title']}; font-size: 13px;
    selection-background-color: rgba(10,132,255,0.5);
}}
QLineEdit:focus {{ border: 1.5px solid {t['input_focus_border']}; background: {t['input_focus_bg']}; }}
QCheckBox {{ spacing: 10px; color: {t['text']}; font-size: 13px; background: transparent; }}
QCheckBox::indicator {{
    width: 22px; height: 22px; border-radius: 7px;
    background: {t['check_bg']}; border: 1.5px solid {t['check_border']};
}}
QCheckBox::indicator:hover {{ background: {t['surface_hover']}; border-color: {t['border_hover']}; }}
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0A84FF, stop:1 #0066DD);
    border: 1.5px solid rgba(10,132,255,0.7);
}}
QComboBox {{
    background: {t['input_bg']}; border: 1px solid {t['input_border']};
    border-radius: 10px; padding: 8px 14px; color: {t['text_title']}; font-size: 13px; min-height: 20px;
}}
QComboBox:hover {{ border-color: {t['border_hover']}; background: {t['surface_hover']}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{
    image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
    border-top: 5px solid {t['text_dim']}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {t['combo_dropdown_bg']}; border: 1px solid {t['border']};
    border-radius: 10px; selection-background-color: {t['list_selected']};
    color: {t['text']}; padding: 4px; outline: none;
}}
QSlider::groove:horizontal {{ background: {t['slider_groove']}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0A84FF, stop:1 #0066DD);
    width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; border: 1px solid rgba(10,132,255,0.5);
}}
QSlider::handle:horizontal:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #409CFF, stop:1 #0A84FF); }}
QSlider::sub-page:horizontal {{ background: {t['slider_sub']}; border-radius: 3px; }}
QSpinBox, QDoubleSpinBox {{
    background: {t['input_bg']}; border: 1px solid {t['input_border']};
    border-radius: 10px; padding: 8px 14px; color: {t['text_title']}; font-size: 13px; min-height: 20px;
}}
QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {t['border_hover']}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ background: transparent; border: none; width: 20px; }}
QListWidget {{
    background: {t['list_bg']}; border: 1px solid {t['border']};
    border-radius: 14px; padding: 6px; outline: none;
}}
QListWidget::item {{
    padding: 10px 12px; border-radius: 10px; margin: 2px 0; color: {t['text']}; border: none;
}}
QListWidget::item:selected {{ background: {t['list_selected']}; }}
QListWidget::item:hover:!selected {{ background: {t['list_hover']}; }}
QTextEdit {{
    background: {t['list_bg']}; border: 1px solid {t['border']};
    border-radius: 14px; padding: 12px; color: {t['text_dim']};
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace; font-size: 12px;
}}
QProgressBar {{
    background: {t['progress_bg']}; border: 1px solid {t['progress_border']};
    border-radius: 12px; text-align: center; color: {t['text']}; font-size: 12px; font-weight: 600; min-height: 26px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0A84FF, stop:1 #5AC8FA); border-radius: 11px;
}}
QGroupBox {{
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    border-radius: 18px; margin-top: 22px; padding: 22px 16px 16px 16px;
    font-size: 11px; font-weight: bold; color: {t['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 20px; top: 2px; padding: 0 10px;
    color: {t['text_muted']}; font-size: 11px; letter-spacing: 1.5px;
}}
QScrollArea {{ background: transparent; border: none; }}
QToolTip {{
    background: {t['tooltip_bg']}; border: 1px solid {t['border']};
    border-radius: 8px; padding: 8px 12px; color: {t['text']}; font-size: 12px;
}}
QMessageBox {{ background: {t['bg_primary']}; }}
QMessageBox QLabel {{ color: {t['text']}; }}
QMessageBox QPushButton {{ min-width: 80px; min-height: 32px; }}
QStatusBar {{
    background: {t['status_bg']}; border-top: 1px solid {t['status_border']};
    color: {t['text_muted']}; font-size: 11px;
}}
QStatusBar QLabel {{ color: {t['text_muted']}; font-size: 11px; padding: 2px 8px; }}
QMenu {{
    background: {t['menu_bg']}; border: 1px solid {t['border']};
    border-radius: 10px; padding: 6px;
}}
QMenu::item {{ padding: 8px 24px; border-radius: 6px; color: {t['text']}; }}
QMenu::item:selected {{ background: {t['list_selected']}; }}
QMenu::separator {{ height: 1px; background: {t['border']}; margin: 4px 8px; }}
QRadioButton {{ color: {t['text']}; font-size: 13px; background: transparent; spacing: 8px; }}
QRadioButton::indicator {{
    width: 18px; height: 18px; border-radius: 9px;
    background: {t['check_bg']}; border: 1.5px solid {t['check_border']};
}}
QRadioButton::indicator:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0A84FF, stop:1 #0066DD);
    border: 1.5px solid rgba(10,132,255,0.7);
}}
"""


def get_stylesheet(theme='dark') -> str:
    return _gen_stylesheet(THEMES.get(theme, THEMES['dark']))


# Для обратной совместимости
GLASS_STYLESHEET = _gen_stylesheet(THEMES['dark'])

# ══════════════════════════════════════════════════════════════════════════════
#  КНОПКИ (не зависят от темы — accent всегда синий)
# ══════════════════════════════════════════════════════════════════════════════

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

ACCENT_BTN = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0A84FF, stop:1 #0060CC);
        border: 1px solid rgba(10,132,255,0.45); border-radius: 14px; padding: 14px 30px;
        color: white; font-size: 15px; font-weight: bold; letter-spacing: 0.5px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #409CFF, stop:1 #0A84FF);
        border-color: rgba(10,132,255,0.65);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0066CC, stop:1 #004499);
    }
    QPushButton:disabled {
        background: rgba(10,132,255,0.15); color: rgba(255,255,255,0.30);
        border-color: rgba(10,132,255,0.10);
    }
"""

ACCENT_BTN_SM = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 rgba(10,132,255,0.35), stop:1 rgba(10,132,255,0.20));
        border: 1px solid rgba(10,132,255,0.30); border-radius: 12px; padding: 10px 18px;
        color: #5AC8FA; font-size: 13px; font-weight: 600;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 rgba(10,132,255,0.45), stop:1 rgba(10,132,255,0.30));
        border-color: rgba(10,132,255,0.50);
    }
    QPushButton:pressed { background: rgba(10,132,255,0.15); }
"""

DANGER_BTN = """
    QPushButton {
        background: rgba(255,69,58,0.12); border: 1px solid rgba(255,69,58,0.25);
        border-radius: 12px; padding: 10px 18px;
        color: #FF6961; font-size: 13px; font-weight: 500;
    }
    QPushButton:hover { background: rgba(255,69,58,0.20); border-color: rgba(255,69,58,0.40); }
    QPushButton:pressed { background: rgba(255,69,58,0.08); }
"""

PRESET_ACTIVE = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0A84FF, stop:1 #0060CC);
        border: 1.5px solid rgba(10,132,255,0.7); border-radius: 12px; padding: 10px 18px;
        color: white; font-size: 13px; font-weight: 700;
    }
"""

SLIDER_NEUTRAL_LABEL = "color: rgba(255,255,255,0.30); font-size: 12px;"
SLIDER_ACTIVE_LABEL = "color: rgba(90,200,250,0.90); font-size: 12px; font-weight: 600;"
