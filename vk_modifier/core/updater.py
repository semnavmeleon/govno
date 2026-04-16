"""Проверка обновлений через GitHub Releases API."""

import logging
from PyQt5.QtCore import QThread, pyqtSignal

from ..constants import APP_VERSION, UPDATE_CHECK_URL

logger = logging.getLogger('vk_modifier.updater')


def _parse_version(v: str) -> tuple[int, ...]:
    """'2.1.0' -> (2, 1, 0)"""
    try:
        return tuple(int(x) for x in v.strip().lstrip('vV').split('.'))
    except Exception:
        return (0,)


class UpdateChecker(QThread):
    """Фоновая проверка обновлений. Эмитит результат."""
    update_available = pyqtSignal(str, str)  # new_version, download_url
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)  # error message

    def run(self):
        if not UPDATE_CHECK_URL:
            self.no_update.emit()
            return

        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                UPDATE_CHECK_URL,
                headers={'Accept': 'application/vnd.github.v3+json',
                         'User-Agent': 'VKTrackModifier'},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            tag = data.get('tag_name', '')
            remote_ver = _parse_version(tag)
            local_ver = _parse_version(APP_VERSION)

            if remote_ver > local_ver:
                download_url = ''
                for asset in data.get('assets', []):
                    name = asset.get('name', '').lower()
                    if name.endswith('.exe') or name.endswith('.zip'):
                        download_url = asset.get('browser_download_url', '')
                        break
                if not download_url:
                    download_url = data.get('html_url', '')
                logger.info(f"Доступно обновление: {tag}")
                self.update_available.emit(tag, download_url)
            else:
                self.no_update.emit()

        except Exception as e:
            logger.debug(f"Update check failed: {e}")
            self.check_failed.emit(str(e))
