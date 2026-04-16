"""Кастомные виджеты."""

import os
import struct
import logging
import subprocess

from PyQt5.QtWidgets import (
    QGroupBox, QListWidget, QLabel, QTabBar, QWidget,
    QVBoxLayout, QStackedWidget, QHBoxLayout, QSlider, QAbstractItemView,
    QMenu, QAction, QGraphicsDropShadowEffect, QPushButton, QStyle,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread, QUrl
from PyQt5.QtGui import (
    QPixmap, QColor, QFont, QPainter, QPen, QBrush, QLinearGradient,
    QDragEnterEvent, QDropEvent,
)

from .styles import SLIDER_NEUTRAL_LABEL, SLIDER_ACTIVE_LABEL

logger = logging.getLogger('vk_modifier.widgets')


# ══════════════════════════════════════════════════════════════════════════════
#  BASIC WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class GlassCard(QGroupBox):
    """Стеклянная карточка-секция."""
    def __init__(self, title=""):
        super().__init__(title.upper() if title else "")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class CoverPreviewLabel(QLabel):
    """Превью обложки с кликом."""
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(160, 160)
        self._apply_empty_style()

    def _apply_empty_style(self):
        self.setStyleSheet("""
            QLabel {
                border: 1.5px dashed rgba(255,255,255,0.12); border-radius: 18px;
                background: rgba(255,255,255,0.03); color: rgba(255,255,255,0.25); font-size: 11px;
            }
            QLabel:hover { border-color: rgba(255,255,255,0.22); background: rgba(255,255,255,0.05); }
        """)

    def _apply_filled_style(self):
        self.setStyleSheet("""
            QLabel {
                border: 1.5px solid rgba(255,255,255,0.10); border-radius: 18px;
                background: rgba(255,255,255,0.03);
            }
            QLabel:hover { border-color: rgba(255,255,255,0.22); }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_pixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            super().setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setText("")
            self._apply_filled_style()
        else:
            self.setText("Обложка\nнажмите\nдля выбора")
            super().setPixmap(QPixmap())
            self._apply_empty_style()


# ══════════════════════════════════════════════════════════════════════════════
#  FILE LIST (drag-drop + reorder + context menu)
# ══════════════════════════════════════════════════════════════════════════════

class FileListWidget(QListWidget):
    """Список файлов с drag-and-drop, мульти-выделением, reorder и контекстным меню."""
    files_dropped = pyqtSignal(list)
    context_action = pyqtSignal(str, list)
    order_changed = pyqtSignal()

    SUPPORTED_EXT = {'.mp3'}

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                local = url.toLocalFile()
                if os.path.isdir(local):
                    for root, _, files in os.walk(local):
                        for f in files:
                            if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXT:
                                paths.append(os.path.join(root, f))
                elif os.path.splitext(local)[1].lower() in self.SUPPORTED_EXT:
                    paths.append(local)
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            # Internal reorder
            super().dropEvent(event)
            self.order_changed.emit()

    def get_selected_indices(self) -> list[int]:
        return sorted(set(idx.row() for idx in self.selectedIndexes()))

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        indices = self.get_selected_indices()
        count = len(indices)
        suffix = f" ({count})" if count > 1 else ""

        actions = [
            ("play", "Прослушать"),
            ("cover", f"Задать обложку{suffix}..."),
            ("meta", f"Задать метаданные{suffix}..."),
            ("sep1", None),
            ("select_all", "Выделить все"),
            ("remove", f"Удалить из списка{suffix}"),
            ("open_folder", "Открыть папку файла"),
        ]

        for key, label in actions:
            if label is None:
                menu.addSeparator()
            else:
                action = menu.addAction(label)
                action.setData(key)
                if key in ("play", "open_folder") and count != 1:
                    action.setEnabled(False)
                if key in ("remove", "cover", "meta") and count == 0:
                    action.setEnabled(False)

        chosen = menu.exec_(self.mapToGlobal(pos))
        if chosen:
            self.context_action.emit(chosen.data(), indices)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDER WITH LABEL
# ══════════════════════════════════════════════════════════════════════════════

class SliderWithLabel(QWidget):
    """Слайдер с отображением значения. Нейтральная позиция = эффект выключен."""
    valueChanged = pyqtSignal(float)

    def __init__(self, label: str, min_val: float, max_val: float,
                 neutral: float, step: float = 1.0,
                 suffix: str = '', decimals: int = 2):
        super().__init__()
        self._min = min_val
        self._max = max_val
        self._neutral = neutral
        self._step = step
        self._suffix = suffix
        self._decimals = decimals
        self._steps = int((max_val - min_val) / step)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._label = QLabel(label)
        self._label.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 12px; min-width: 140px;")
        lay.addWidget(self._label)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, self._steps)
        self._slider.setValue(self._val_to_pos(neutral))
        self._slider.valueChanged.connect(self._on_changed)
        lay.addWidget(self._slider, 1)

        self._value_label = QLabel()
        self._value_label.setMinimumWidth(70)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._value_label)

        self._update_display()

    def _val_to_pos(self, val: float) -> int:
        return round((val - self._min) / self._step)

    def _pos_to_val(self, pos: int) -> float:
        return self._min + pos * self._step

    def value(self) -> float:
        return self._pos_to_val(self._slider.value())

    def setValue(self, val: float):
        self._slider.setValue(self._val_to_pos(val))

    def is_active(self) -> bool:
        return abs(self.value() - self._neutral) > self._step * 0.5

    def _on_changed(self, pos):
        self._update_display()
        self.valueChanged.emit(self.value())

    def _update_display(self):
        val = self.value()
        active = self.is_active()
        if self._decimals == 0:
            text = f"{int(val)}{self._suffix}"
        else:
            text = f"{val:.{self._decimals}f}{self._suffix}"
        if not active:
            text = "Выкл"
            self._value_label.setStyleSheet(SLIDER_NEUTRAL_LABEL)
        else:
            self._value_label.setStyleSheet(SLIDER_ACTIVE_LABEL)
        self._value_label.setText(text)


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════

class GlassTabBar(QTabBar):
    """Таб-бар с бейджами-счётчиками."""
    def __init__(self):
        super().__init__()
        self._badges = {}
        self.setStyleSheet("""
            QTabBar { background: transparent; border: none; }
            QTabBar::tab {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.07);
                border-bottom: none;
                border-top-left-radius: 12px; border-top-right-radius: 12px;
                padding: 10px 22px 10px 16px; margin-right: 4px;
                color: rgba(255,255,255,0.45); font-size: 13px; font-weight: 600;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255,0.07);
                border-color: rgba(255,255,255,0.12);
                color: rgba(255,255,255,0.92);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255,255,255,0.06);
                color: rgba(255,255,255,0.65);
            }
        """)

    def set_badge(self, index, count):
        self._badges[index] = count
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        for idx, count in self._badges.items():
            if count <= 0 or idx >= self.count():
                continue
            rect = self.tabRect(idx)
            badge_size = 20
            bx = rect.right() - badge_size - 6
            by = rect.top() + (rect.height() - badge_size) // 2
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(10, 132, 255))
            painter.drawEllipse(bx, by, badge_size, badge_size)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(bx, by, badge_size, badge_size, Qt.AlignCenter, str(count))
        painter.end()

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(size.width() + 28)
        return size


class GlassTabWidget(QWidget):
    """GlassTabBar + QStackedWidget."""
    def __init__(self):
        super().__init__()
        self.tab_bar = GlassTabBar()
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.tab_bar)
        lay.addWidget(self.stack)
        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)

    def add_tab(self, widget, title):
        idx = self.stack.addWidget(widget)
        self.tab_bar.addTab(title)
        return idx

    def set_badge(self, index, count):
        self.tab_bar.set_badge(index, count)


# ══════════════════════════════════════════════════════════════════════════════
#  LOG HANDLER (thread-safe logging into QTextEdit)
# ══════════════════════════════════════════════════════════════════════════════

class QTextEditLogHandler(logging.Handler):
    """Лог-хендлер, пишущий в QTextEdit через signal (thread-safe)."""

    class _Emitter(QWidget):
        log_signal = pyqtSignal(str)

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self._emitter = self._Emitter()
        self._emitter.log_signal.connect(self._append)
        self.setFormatter(logging.Formatter(
            '<span style="color:%(color)s">[%(levelname)s] %(name)s: %(message)s</span>'
        ))

    def emit(self, record):
        # Цвет по уровню
        colors = {
            logging.DEBUG: 'rgba(255,255,255,0.35)',
            logging.INFO: 'rgba(90,200,250,0.85)',
            logging.WARNING: 'rgba(255,200,50,0.85)',
            logging.ERROR: 'rgba(255,100,100,0.90)',
        }
        record.color = colors.get(record.levelno, 'rgba(255,255,255,0.65)')
        try:
            msg = self.format(record)
            self._emitter.log_signal.emit(msg)
        except Exception:
            pass

    def _append(self, html):
        self.text_edit.append(html)
        # Автоскролл вниз
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())


# ══════════════════════════════════════════════════════════════════════════════
#  WAVEFORM WIDGET
# ══════════════════════════════════════════════════════════════════════════════

class WaveformLoader(QThread):
    """Загрузка PCM-данных через ffmpeg в фоне."""
    loaded = pyqtSignal(list, float)  # samples, duration_sec

    def __init__(self, file_path, ffmpeg_path='ffmpeg'):
        super().__init__()
        self.file_path = file_path
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        try:
            from ..core.ffmpeg import find_ffmpeg, _STARTUPINFO, _CREATION_FLAGS
            ffmpeg = find_ffmpeg() or 'ffmpeg'
            # Извлечь mono float32 PCM на 8kHz
            proc = subprocess.Popen(
                [ffmpeg, '-i', self.file_path, '-f', 'f32le', '-ac', '1',
                 '-ar', '8000', '-v', 'quiet', '-'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                startupinfo=_STARTUPINFO, creationflags=_CREATION_FLAGS,
            )
            raw = proc.stdout.read(8000 * 4 * 600)  # макс 600 сек
            proc.wait()

            if not raw:
                self.loaded.emit([], 0.0)
                return

            n_samples = len(raw) // 4
            samples = list(struct.unpack(f'{n_samples}f', raw[:n_samples * 4]))
            duration = n_samples / 8000.0

            # Даунсемплинг до ~2000 точек
            target = 2000
            if n_samples > target:
                step = n_samples // target
                downsampled = []
                for i in range(0, n_samples - step, step):
                    chunk = samples[i:i + step]
                    downsampled.append(max(abs(s) for s in chunk))
                samples = downsampled

            self.loaded.emit(samples, duration)
        except Exception as e:
            logger.warning(f"Waveform load error: {e}")
            self.loaded.emit([], 0.0)


class WaveformWidget(QWidget):
    """Визуализация волны трека. Кликом можно задать точку обрезки."""
    position_clicked = pyqtSignal(float)  # секунды

    def __init__(self):
        super().__init__()
        self._samples = []
        self._duration = 0.0
        self._trim_start = 0.0
        self._cut_start = 0.0
        self._cut_end = 0.0
        self._loader = None
        self._loading = False
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self.setStyleSheet("background: transparent;")

    def load_track(self, file_path):
        self._samples = []
        self._loading = True
        self.update()
        self._loader = WaveformLoader(file_path)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.start()

    def _on_loaded(self, samples, duration):
        self._samples = samples
        self._duration = duration
        self._loading = False
        self.update()

    def set_markers(self, trim_start=0.0, cut_start=0.0, cut_end=0.0):
        self._trim_start = trim_start
        self._cut_start = cut_start
        self._cut_end = cut_end
        self.update()

    def mousePressEvent(self, event):
        if self._duration > 0 and self._samples:
            x_ratio = event.x() / max(self.width(), 1)
            sec = x_ratio * self._duration
            self.position_clicked.emit(sec)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Фон
        painter.fillRect(0, 0, w, h, QColor(255, 255, 255, 8))

        if self._loading:
            painter.setPen(QColor(255, 255, 255, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "Загрузка волны...")
            painter.end()
            return

        if not self._samples:
            painter.setPen(QColor(255, 255, 255, 40))
            painter.drawText(self.rect(), Qt.AlignCenter, "Нет данных")
            painter.end()
            return

        n = len(self._samples)
        mid = h / 2
        bar_w = max(w / n, 1)

        # Отрисовка маркеров (trim, cut)
        if self._duration > 0:
            # Trim зона (красная)
            if self._trim_start > 0:
                trim_x = int(self._trim_start / self._duration * w)
                painter.fillRect(0, 0, trim_x, h, QColor(255, 50, 50, 40))

            # Cut зона (жёлтая)
            if self._cut_start > 0 and self._cut_end > self._cut_start:
                x1 = int(self._cut_start / self._duration * w)
                x2 = int(self._cut_end / self._duration * w)
                painter.fillRect(x1, 0, x2 - x1, h, QColor(255, 200, 50, 40))

        # Волна
        max_sample = max(self._samples) if self._samples else 1.0
        if max_sample == 0:
            max_sample = 1.0

        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(10, 132, 255, 200))
        gradient.setColorAt(0.5, QColor(90, 200, 250, 180))
        gradient.setColorAt(1, QColor(10, 132, 255, 200))

        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)

        for i, sample in enumerate(self._samples):
            x = int(i * bar_w)
            amp = abs(sample) / max_sample
            bar_h = max(int(amp * mid * 0.9), 1)
            painter.drawRect(x, int(mid - bar_h), max(int(bar_w) - 1, 1), bar_h * 2)

        # Рамка
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)

        painter.end()


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIO PLAYER
# ══════════════════════════════════════════════════════════════════════════════

class AudioPlayerWidget(QWidget):
    """Встроенный аудиоплеер с A/B сравнением."""

    def __init__(self):
        super().__init__()
        self._player = None
        self._current_file = ''
        self._ab_original = ''
        self._ab_processed = ''
        self._is_b = False
        self._available = False

        try:
            from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
            self._player = QMediaPlayer()
            self._available = True
        except ImportError:
            pass

        self._build_ui()

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(6)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(32, 32)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background: rgba(10,132,255,0.3); border: 1px solid rgba(10,132,255,0.4);
                border-radius: 16px; color: white; font-size: 14px;
            }
            QPushButton:hover { background: rgba(10,132,255,0.5); }
        """)
        self.btn_play.clicked.connect(self._toggle_play)
        lay.addWidget(self.btn_play)

        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(32, 32)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
                border-radius: 16px; color: white; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
        """)
        self.btn_stop.clicked.connect(self._stop)
        lay.addWidget(self.btn_stop)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self._seek)
        lay.addWidget(self.seek_slider, 1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 11px; min-width: 80px;")
        lay.addWidget(self.time_label)

        self.btn_ab = QPushButton("A/B")
        self.btn_ab.setFixedSize(40, 32)
        self.btn_ab.setToolTip("Переключить оригинал / обработанный")
        self.btn_ab.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px; color: rgba(255,255,255,0.6); font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
        """)
        self.btn_ab.clicked.connect(self._toggle_ab)
        self.btn_ab.setEnabled(False)
        lay.addWidget(self.btn_ab)

        if not self._available:
            self.setToolTip("QMediaPlayer недоступен. pip install PyQt5-multimedia")

        if self._player:
            self._player.positionChanged.connect(self._on_position)
            self._player.durationChanged.connect(self._on_duration)

        self.setMaximumHeight(44)

    def load_file(self, path):
        """Загрузить файл для воспроизведения."""
        if not self._available or not path or not os.path.isfile(path):
            return
        self._current_file = path
        self._ab_original = path
        from PyQt5.QtMultimedia import QMediaContent
        self._player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))

    def set_processed(self, path):
        """Установить обработанный файл для A/B сравнения."""
        self._ab_processed = path
        self.btn_ab.setEnabled(bool(path and os.path.isfile(path)))

    def _toggle_play(self):
        if not self._player:
            return
        from PyQt5.QtMultimedia import QMediaPlayer
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.pause()
            self.btn_play.setText("▶")
        else:
            self._player.play()
            self.btn_play.setText("⏸")

    def _stop(self):
        if self._player:
            self._player.stop()
            self.btn_play.setText("▶")

    def _seek(self, pos):
        if self._player and self._player.duration() > 0:
            self._player.setPosition(int(pos / 1000 * self._player.duration()))

    def _toggle_ab(self):
        if not self._ab_processed:
            return
        self._is_b = not self._is_b
        path = self._ab_processed if self._is_b else self._ab_original
        was_playing = False
        pos = 0
        from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
        if self._player.state() == QMediaPlayer.PlayingState:
            was_playing = True
            pos = self._player.position()
        self._player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        if was_playing:
            self._player.play()
            self._player.setPosition(pos)
        self.btn_ab.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(10,132,255,0.4)' if self._is_b else 'rgba(255,255,255,0.06)'};
                border: 1px solid {'rgba(10,132,255,0.6)' if self._is_b else 'rgba(255,255,255,0.10)'};
                border-radius: 8px; color: {'white' if self._is_b else 'rgba(255,255,255,0.6)'};
                font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(10,132,255,0.5); }}
        """)

    def _on_position(self, pos_ms):
        dur = self._player.duration() if self._player else 0
        if dur > 0:
            self.seek_slider.setValue(int(pos_ms / dur * 1000))
        self.time_label.setText(f"{self._fmt(pos_ms)} / {self._fmt(dur)}")

    def _on_duration(self, dur_ms):
        self.time_label.setText(f"0:00 / {self._fmt(dur_ms)}")

    @staticmethod
    def _fmt(ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"
