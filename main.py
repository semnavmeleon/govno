"""VK Track Modifier v2 — точка входа."""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


def setup_logging():
    logger = logging.getLogger('vk_modifier')
    logger.setLevel(logging.DEBUG)

    fh = RotatingFileHandler(
        'vk_modifier.log', maxBytes=1_000_000, backupCount=5, encoding='utf-8'
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(ch)

    return logger


def main():
    logger = setup_logging()
    logger.info("=== VK Track Modifier DAW Edition запущен ===")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)

    from ui.daw_interface import DAWMainWindow
    window = DAWMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
