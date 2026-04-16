"""
UI компоненты для VK Modifier
"""

from PyQt5.QtWidgets import QLabel, QGroupBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QColor


class CoverPreviewLabel(QLabel):
    """Кастомный QLabel для предпросмотра обложки с обработкой клика"""
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #777;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #aaa;
                font-size: 11px;
            }
            QLabel:hover {
                border: 1px solid #5a5a5a;
                background-color: #333;
            }
        """)
        self.setText("Обложка\nнажмите для\nвыбора")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_pixmap(self, pixmap):
        """Устанавливает pixmap с автоматическим масштабированием"""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)
            self.setText("")
        else:
            self.setText("Обложка\nнажмите для\nвыбора")
            super().setPixmap(QPixmap())


class CollapsibleGroup(QGroupBox):
    """Сворачиваемая группа с кастомным стилем"""

    def __init__(self, title):
        super().__init__(title)
        self.setCheckable(True)
        self.setChecked(True)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QGroupBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #666;
                border-radius: 2px;
                background: #2a2a2a;
            }
            QGroupBox::indicator:checked {
                background: #666;
            }
        """)
