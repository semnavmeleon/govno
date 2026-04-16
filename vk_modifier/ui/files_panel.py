"""Панель управления файлами."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal


class FilesPanel(QFrame):
    """Панель со списком файлов."""
    
    file_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setObjectName('panelFrame')
        
        self._files = []
        self._selected_index = -1
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        header = QLabel("📁 ФАЙЛЫ")
        header.setObjectName('headerLabel')
        layout.addWidget(header)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_add.setObjectName('primaryBtn')
        self.btn_add.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton("🗑️ Удалить")
        self.btn_remove.setObjectName('dangerBtn')
        self.btn_remove.setMinimumHeight(40)
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self.btn_remove)
        
        layout.addLayout(btn_layout)
        
        # Список файлов
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background: #1a1a2e;
                border: 2px solid #2a2a3e;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 4px 0;
                color: #ffffff;
                background: #16213e;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f3460, stop:1 #00adb5);
                border-left: 4px solid #00adb5;
            }
            QListWidget::item:hover {
                background: #0f3460;
            }
        """)
        self.file_list.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self.file_list, 1)
        
        # Инфо
        self.info_label = QLabel("Файлов: 0")
        self.info_label.setStyleSheet("color: #606060; font-size: 11px;")
        layout.addWidget(self.info_label)
        
    def add_files(self, paths):
        """Добавить файлы."""
        for path in paths:
            if path not in self._files:
                self._files.append(path)
                name = os.path.basename(path)
                item = QListWidgetItem(f"🎵 {name}")
                self.file_list.addItem(item)
        self._update_info()
        
    def _on_selection(self):
        """Изменение выделения."""
        items = self.file_list.selectedItems()
        if items:
            self._selected_index = self.file_list.row(items[0])
            self.btn_remove.setEnabled(True)
            self.file_selected.emit(self._selected_index)
        else:
            self._selected_index = -1
            self.btn_remove.setEnabled(False)
            
    def _remove_selected(self):
        """Удалить выбранный файл."""
        items = self.file_list.selectedItems()
        if items:
            index = self.file_list.row(items[0])
            self.file_list.takeItem(index)
            self._files.pop(index)
            self._update_info()
            
    def _update_info(self):
        """Обновить информацию."""
        count = len(self._files)
        total_size = sum(os.path.getsize(f) for f in self._files if os.path.exists(f)) / (1024 * 1024)
        self.info_label.setText(f"Файлов: {count} · {total_size:.1f} MB")
        
    def get_selected_index(self):
        return self._selected_index
        
    def get_file_path(self, index):
        return self._files[index] if 0 <= index < len(self._files) else ''
