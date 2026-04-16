"""Стили для UI компонентов."""

# Стили для слайдеров
SLIDER_NEUTRAL_LABEL = "color: rgba(255,255,255,0.35); font-size: 12px;"
SLIDER_ACTIVE_LABEL = "color: rgba(59,130,246,0.85); font-size: 12px; font-weight: 600;"

# Стили для кнопок
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
