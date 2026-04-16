"""Виджет метаданных."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QFileDialog,
    QScrollArea, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap


class MetadataWidget(QScrollArea):
    """Виджет редактирования метаданных."""
    
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
        header = QLabel("🎼 МЕТАДАННЫЕ")
        header.setObjectName('headerLabel')
        layout.addWidget(header)
        
        # Шаблон имени
        name_frame = QFrame()
        name_frame.setObjectName('cardFrame')
        name_layout = QGridLayout(name_frame)
        name_layout.setSpacing(10)
        
        name_layout.addWidget(QLabel("Шаблон имени:"), 0, 0)
        self.filename_template = QLineEdit()
        self.filename_template.setPlaceholderText("{prefix}_{counter:03d}_{original_name}")
        self.filename_template.setText("{prefix}_{counter:03d}_{original_name}")
        name_layout.addWidget(self.filename_template, 0, 1)
        
        name_layout.addWidget(QLabel("Префикс:"), 1, 0)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("VK")
        name_layout.addWidget(self.prefix_edit, 1, 1)
        
        name_layout.addWidget(QLabel("Тег:"), 2, 0)
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("REUPLOAD, REMIX...")
        name_layout.addWidget(self.tag_edit, 2, 1)
        
        layout.addWidget(name_frame)
        
        # Теги ID3
        tags_frame = QFrame()
        tags_frame.setObjectName('cardFrame')
        tags_layout = QGridLayout(tags_frame)
        tags_layout.setSpacing(10)
        
        tags_layout.addWidget(QLabel("Название:"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Оставить оригинал")
        tags_layout.addWidget(self.title_edit, 0, 1)
        
        tags_layout.addWidget(QLabel("Исполнитель:"), 1, 0)
        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Оставить оригинал")
        tags_layout.addWidget(self.artist_edit, 1, 1)
        
        tags_layout.addWidget(QLabel("Альбом:"), 2, 0)
        self.album_edit = QLineEdit()
        self.album_edit.setPlaceholderText("Оставить оригинал")
        tags_layout.addWidget(self.album_edit, 2, 1)
        
        tags_layout.addWidget(QLabel("Год:"), 3, 0)
        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("2024")
        tags_layout.addWidget(self.year_edit, 3, 1)
        
        tags_layout.addWidget(QLabel("Жанр:"), 4, 0)
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Pop, Rock...")
        tags_layout.addWidget(self.genre_edit, 4, 1)
        
        layout.addWidget(tags_frame)
        
        # Обложка
        cover_frame = QFrame()
        cover_frame.setObjectName('cardFrame')
        cover_layout = QVBoxLayout(cover_frame)
        cover_layout.setSpacing(10)
        
        cover_title = QLabel("🖼️ ОБЛОЖКА")
        cover_title.setObjectName('sectionLabel')
        cover_layout.addWidget(cover_title)
        
        self.cover_label = QLabel("Нет обложки")
        self.cover_label.setStyleSheet("""
            color: #606060;
            font-size: 12px;
            padding: 20px;
            background: #1a1a2e;
            border: 2px dashed #2a2a3e;
            border-radius: 8px;
            text-align: center;
        """)
        self.cover_label.setAlignment(Qt.AlignCenter)
        cover_layout.addWidget(self.cover_label)
        
        self.btn_cover = QPushButton("📁 Выбрать обложку")
        self.btn_cover.setObjectName('secondaryBtn')
        self.btn_cover.clicked.connect(self._select_cover)
        cover_layout.addWidget(self.btn_cover)
        
        layout.addWidget(cover_frame)
        
        # Экспорт
        export_frame = QFrame()
        export_frame.setObjectName('cardFrame')
        export_layout = QGridLayout(export_frame)
        export_layout.setSpacing(10)
        
        export_layout.addWidget(QLabel("Качество MP3:"), 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["320 kbps", "245 kbps", "175 kbps", "130 kbps"])
        self.quality_combo.setCurrentIndex(0)
        export_layout.addWidget(self.quality_combo, 0, 1)
        
        export_layout.addWidget(QLabel("Потоков:"), 1, 0)
        self.workers_spin = QComboBox()
        self.workers_spin.addItems(["1", "2", "3", "4"])
        self.workers_spin.setCurrentIndex(1)
        export_layout.addWidget(self.workers_spin, 1, 1)
        
        self.chk_delete = QCheckBox("Удалить оригиналы после обработки")
        self.chk_delete.setStyleSheet("color: #ff4757; font-size: 12px;")
        export_layout.addWidget(self.chk_delete, 2, 0, 1, 2)
        
        layout.addWidget(export_frame)
        
        layout.addStretch()
        self.setWidget(content)
        
    def load_track(self, track):
        """Загрузить данные трека."""
        if track.title:
            self.title_edit.setPlaceholderText(track.title)
        if track.artist:
            self.artist_edit.setPlaceholderText(track.artist)
        if track.cover_data:
            self._show_cover(track.cover_data)
            
    def _select_cover(self):
        """Выбрать обложку."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            with open(path, 'rb') as f:
                data = f.read()
            self._show_cover(data)
            
    def _show_cover(self, data):
        """Показать обложку."""
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            scaled = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.cover_label.setPixmap(scaled)
            self.cover_label.setText("")
            self.cover_label.setStyleSheet("""
                border: 2px solid #00adb5;
                border-radius: 8px;
                background: #1a1a2e;
            """)
            
    def get_settings(self):
        quality_map = {
            0: '0',  # 320 kbps
            1: '2',  # 245 kbps
            2: '5',  # 175 kbps
            3: '7',  # 130 kbps
        }
        
        return {
            'filename_template': self.filename_template.text(),
            'brand_prefix': self.prefix_edit.text(),
            'brand_tag': self.tag_edit.text(),
            'title': self.title_edit.text(),
            'artist': self.artist_edit.text(),
            'album': self.album_edit.text(),
            'year': self.year_edit.text(),
            'genre': self.genre_edit.text(),
            'quality': quality_map.get(self.quality_combo.currentIndex(), '2'),
            'max_workers': int(self.workers_spin.currentText()),
            'delete_originals': self.chk_delete.isChecked(),
        }
