"""
Методы обработки событий и логика работы для VK Track Modifier GUI
Этот модуль содержит методы которые должны быть добавлены в класс VKTrackModifier
"""

import os
import random
import subprocess
import tempfile
import hashlib
import sys
from datetime import timedelta

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QColor


def add_event_handlers_to_main(main_file_path: str):
    """Добавляет обработчики событий в главный файл"""
    
    event_handlers_code = '''
    # ==================== МЕТОДЫ ОБРАБОТКИ СОБЫТИЙ ====================
    
    def _on_merge_toggled(self, checked):
        """Обработчик переключения режима сращивания"""
        self.btn_merge_track.setEnabled(checked)
        if not checked:
            self.extra_track_path = ""
            self.merge_track_label.setText("")

    def _select_merge_track(self):
        """Выбор трека для сращивания"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите трек для сращивания", "", "MP3 files (*.mp3)"
        )
        if file_path:
            self.extra_track_path = file_path
            self.merge_track_label.setText(f"Выбран: {os.path.basename(file_path)}")

    def _random_cover(self):
        """Генерация случайной обложки"""
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        pixmap = QPixmap(500, 500)
        pixmap.fill(QColor(
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        ))

        temp_cover = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        pixmap.save(temp_cover.name)
        temp_cover.close()

        track = self.tracks_info[self.current_track_index]
        with open(temp_cover.name, 'rb') as f:
            track.cover_data = f.read()
        track.cover_mime = 'image/png'

        self.cover_preview.set_pixmap(pixmap)
        self.cover_info.setText("Случайная обложка")
        self.btn_cover_remove.setEnabled(True)

        try:
            os.unlink(temp_cover.name)
        except Exception:
            pass

    def _random_metadata(self):
        """Генерация случайных метаданных"""
        titles = ["Track", "Song", "Melody", "Rhythm", "Harmony", "Beat", "Flow", "Vibe", "Sound", "Wave"]
        artists = ["Artist", "Musician", "Producer", "DJ", "Band", "Project", "Studio", "Creator"]
        albums = ["Album", "Collection", "Mix", "Set", "Compilation", "Series", "Volume"]
        genres = ["Pop", "Rock", "Electronic", "Hip Hop", "Jazz", "Classical", "Ambient", "Dance"]

        self.edit_title.setText(f"{random.choice(titles)} {random.randint(1, 999)}")
        self.edit_artist.setText(f"{random.choice(artists)} {random.randint(1, 99)}")
        self.edit_album.setText(f"{random.choice(albums)} {random.randint(2020, 2024)}")
        self.edit_year.setText(str(random.randint(2000, 2024)))
        self.edit_genre.setText(random.choice(genres))

    def _preview_effects(self):
        """Предпросмотр эффектов (15 секунд)"""
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        settings = self._get_settings()
        track = self.tracks_info[self.current_track_index]

        temp_preview = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_preview.close()

        filters = FilterBuilder.build_filters(settings)

        cmd = ['ffmpeg', '-i', track.file_path, '-t', '15']
        if filters:
            cmd.extend(['-af', filters])
        cmd.extend(['-codec:a', 'libmp3lame', '-q:a', '2', '-y', temp_preview.name])

        try:
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                if sys.platform == 'win32':
                    os.startfile(temp_preview.name)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', temp_preview.name])
                else:
                    subprocess.run(['xdg-open', temp_preview.name])
                QTimer.singleShot(60000, lambda: self._delete_temp_file(temp_preview.name))
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка создания предпросмотра:\\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_temp_file(self, file_path):
        """Удаление временного файла"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass

    def _show_ffmpeg_warning(self):
        """Показ предупреждения об отсутствии FFmpeg"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("FFmpeg не найден")
        msg.setText("Для работы программы требуется FFmpeg")
        msg.setInformativeText("Скачайте FFmpeg с ffmpeg.org и добавьте в PATH")
        msg.exec_()
        self.btn_start.setEnabled(False)

    def _load_settings_from_config(self):
        """Загрузка настроек из конфигурации"""
        self.output_dir = self.config_manager.get('output_dir', '')
        if self.output_dir:
            self.btn_output.setText(f"Папка: {os.path.basename(self.output_dir)}")
        self.chk_preserve_meta.setChecked(self.config_manager.get('preserve_metadata', True))
        self.chk_preserve_cover.setChecked(self.config_manager.get('preserve_cover', True))

    def _add_files(self):
        """Добавление файлов"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите MP3 файлы", "", "MP3 files (*.mp3)"
        )
        if not files:
            return

        for file_path in files:
            if file_path not in self.input_files:
                self.input_files.append(file_path)
                track = TrackInfo(file_path)
                with open(file_path, 'rb') as f:
                    track.set_hash(f.read())
                self.tracks_info.append(track)
                self.file_list.addItem(f"{os.path.basename(file_path)}\\n{track.size_mb:.1f} MB")

        self._update_stats()
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.btn_remove.setEnabled(True)

    def _remove_current_file(self):
        """Удаление текущего файла"""
        current = self.file_list.currentRow()
        if current >= 0:
            self.input_files.pop(current)
            self.tracks_info.pop(current)
            self.file_list.takeItem(current)
            self._update_stats()
            if self.file_list.count() == 0:
                self.btn_remove.setEnabled(False)
                self._clear_editor()

    def _clear_files(self):
        """Очистка списка файлов"""
        self.input_files.clear()
        self.tracks_info.clear()
        self.file_list.clear()
        self._update_stats()
        self.btn_remove.setEnabled(False)
        self._clear_editor()

    def _clear_editor(self):
        """Очистка редактора"""
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()
        self.cover_preview.set_pixmap(None)
        self.cover_info.setText("Нет обложки")
        self.info_text.clear()

    def _on_file_selected(self, index):
        """Обработчик выбора файла"""
        if index < 0 or index >= len(self.tracks_info):
            return

        self.current_track_index = index
        track = self.tracks_info[index]
        self._load_metadata(track)

        info = f"Файл: {track.file_name}\\n"
        info += f"Размер: {track.size_mb:.2f} MB\\n"
        info += f"MD5: {track.file_hash}\\n"
        if track.duration_sec > 0:
            info += f"Длительность: {str(timedelta(seconds=int(track.duration_sec)))}\\n"
        if track.artist or track.title:
            info += f"Оригинал: {track.artist} - {track.title}"

        self.info_text.setText(info)
        self._extract_cover(track)

    def _load_metadata(self, track: TrackInfo):
        """Загрузка метаданных из файла"""
        try:
            audio = MP3(track.file_path)
            track.duration_sec = audio.info.length
            track.bitrate = audio.info.bitrate
            track.sample_rate = audio.info.sample_rate

            if audio.tags:
                if 'TIT2' in audio.tags:
                    track.title = str(audio.tags['TIT2'])
                if 'TPE1' in audio.tags:
                    track.artist = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    track.album = str(audio.tags['TALB'])
                if 'TDRC' in audio.tags:
                    track.year = str(audio.tags['TDRC'])
                if 'TCON' in audio.tags:
                    track.genre = str(audio.tags['TCON'])
        except Exception as e:
            print(f"Error loading metadata: {e}")

    def _extract_cover(self, track: TrackInfo):
        """Извлечение обложки из трека"""
        try:
            audio = MP3(track.file_path)
            if audio.tags:
                for tag in audio.tags.values():
                    if hasattr(tag, 'mime') and hasattr(tag, 'data'):
                        from mutagen.id3 import APIC
                        if isinstance(tag, APIC):
                            track.cover_data = tag.data
                            track.cover_mime = tag.mime
                            pixmap = QPixmap()
                            pixmap.loadFromData(tag.data)
                            self.cover_preview.set_pixmap(pixmap)
                            self.cover_info.setText("Оригинальная обложка")
                            self.btn_cover_remove.setEnabled(True)
                            return

            self.cover_preview.set_pixmap(None)
            track.cover_data = None
            self.cover_info.setText("Нет обложки")
            self.btn_cover_remove.setEnabled(False)
        except Exception as e:
            print(f"Error extracting cover: {e}")

    def _select_cover(self):
        """Выбор обложки"""
        if self.current_track_index < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите трек из списка")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            track = self.tracks_info[self.current_track_index]
            with open(file_path, 'rb') as f:
                track.cover_data = f.read()
            ext = os.path.splitext(file_path)[1].lower()
            track.cover_mime = 'image/png' if ext == '.png' else 'image/jpeg'
            pixmap = QPixmap(file_path)
            self.cover_preview.set_pixmap(pixmap)
            self.cover_info.setText(f"Обложка: {os.path.basename(file_path)}")
            self.btn_cover_remove.setEnabled(True)

    def _remove_cover(self):
        """Удаление обложки"""
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            track.cover_data = None
            self._extract_cover(track)

    def _copy_meta_from_original(self):
        """Копирование метаданных из оригинала"""
        if self.current_track_index >= 0:
            track = self.tracks_info[self.current_track_index]
            self.edit_title.setText(track.title)
            self.edit_artist.setText(track.artist)
            self.edit_album.setText(track.album)
            self.edit_year.setText(track.year)
            self.edit_genre.setText(track.genre)

    def _clear_meta_fields(self):
        """Очистка полей метаданных"""
        self.edit_title.clear()
        self.edit_artist.clear()
        self.edit_album.clear()
        self.edit_year.clear()
        self.edit_genre.clear()

    def _update_stats(self):
        """Обновление статистики"""
        count = len(self.input_files)
        total_size = sum(os.path.getsize(f) for f in self.input_files) / (1024 * 1024)
        self.stats_label.setText(f"Файлов: {count} | Размер: {total_size:.1f} MB")

    def _apply_preset(self, preset: str):
        """Применение пресета"""
        preset_data = PresetManager.get_preset(preset)
        if not preset_data:
            return

        # Применение настроек из пресета к UI элементам
        self.method_trim_silence.setChecked(preset_data.get('trim_silence', False))
        self.method_cut_fragment.setChecked(preset_data.get('cut_fragment', False))
        self.method_fade_out.setChecked(preset_data.get('fade_out', False))
        self.method_broken_duration.setChecked(preset_data.get('broken_duration', False))
        self.broken_type_combo.setCurrentIndex(preset_data.get('broken_type', 0))
        self.method_pitch.setChecked(preset_data.get('pitch', False))
        self.method_silence.setChecked(preset_data.get('silence', False))
        self.method_speed.setChecked(preset_data.get('speed', False))
        
        if preset_data.get('speed_value'):
            speed_values = get_speed_values()
            try:
                idx = speed_values.index(preset_data['speed_value'])
                self.speed_combo.setCurrentIndex(idx)
            except ValueError:
                pass
        
        self.method_eq.setChecked(preset_data.get('eq', False))
        self.method_phase.setChecked(preset_data.get('phase', False))
        self.method_noise.setChecked(preset_data.get('noise', False))
        self.method_compression.setChecked(preset_data.get('compression', False))
        self.method_ultrasound.setChecked(preset_data.get('ultrasound', False))
        self.method_dc_shift.setChecked(preset_data.get('dc_shift', False))
        self.method_merge.setChecked(preset_data.get('merge', False))
        self.method_bitrate_jitter.setChecked(preset_data.get('bitrate_jitter', False))
        self.method_frame_shift.setChecked(preset_data.get('frame_shift', False))
        self.method_fake_metadata.setChecked(preset_data.get('fake_metadata', False))
        self.method_reorder_tags.setChecked(preset_data.get('reorder_tags', False))
        self.chk_reupload.setChecked(preset_data.get('reupload', False))
        
        quality_map = get_quality_map()
        quality_value = preset_data.get('quality', '2')
        for k, v in quality_map.items():
            if v == quality_value:
                self.quality_combo.setCurrentIndex(k)
                break
        
        self.chk_rename.setChecked(preset_data.get('rename_files', True))
        self.chk_preserve_meta.setChecked(preset_data.get('preserve_metadata', True))
        self.chk_preserve_cover.setChecked(preset_data.get('preserve_cover', True))

    def _select_output_dir(self):
        """Выбор папки для сохранения"""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", 
            self.config_manager.get('output_dir', '')
        )
        if directory:
            self.output_dir = directory
            self.config_manager.set('output_dir', directory)
            self.btn_output.setText(f"Папка: {os.path.basename(directory)}")
            self.config_manager.save()

    def _get_settings(self) -> dict:
        """Получение текущих настроек"""
        quality_map = get_quality_map()
        pitch_values = get_pitch_values()
        speed_values = get_speed_values()
        eq_values = get_eq_values()
        phase_values = get_phase_values()
        noise_values = get_noise_values()

        settings = {
            'methods': {
                'trim_silence': self.method_trim_silence.isChecked(),
                'cut_fragment': self.method_cut_fragment.isChecked(),
                'fade_out': self.method_fade_out.isChecked(),
                'broken_duration': self.method_broken_duration.isChecked(),
                'pitch': self.method_pitch.isChecked(),
                'silence': self.method_silence.isChecked(),
                'speed': self.method_speed.isChecked(),
                'eq': self.method_eq.isChecked(),
                'phase': self.method_phase.isChecked(),
                'noise': self.method_noise.isChecked(),
                'compression': self.method_compression.isChecked(),
                'ultrasound': self.method_ultrasound.isChecked(),
                'dc_shift': self.method_dc_shift.isChecked(),
                'merge': self.method_merge.isChecked(),
                'bitrate_jitter': self.method_bitrate_jitter.isChecked(),
                'frame_shift': self.method_frame_shift.isChecked(),
                'fake_metadata': self.method_fake_metadata.isChecked(),
                'reorder_tags': self.method_reorder_tags.isChecked()
            },
            'broken_type': self.broken_type_combo.currentIndex(),
            'trim_duration': self.trim_spin.value(),
            'cut_position_percent': self.cut_position_spin.value(),
            'cut_duration': self.cut_duration_spin.value(),
            'fade_duration': self.fade_duration_spin.value(),
            'pitch_value': pitch_values[self.pitch_combo.currentIndex()],
            'silence_duration': self.silence_spin.value(),
            'speed_value': speed_values[self.speed_combo.currentIndex()],
            'eq_value': eq_values[self.eq_combo.currentIndex()],
            'eq_type': self.eq_combo.currentIndex(),
            'phase_value': phase_values[self.phase_combo.currentIndex()],
            'noise_value': noise_values[self.noise_combo.currentIndex()],
            'quality': quality_map[self.quality_combo.currentIndex()],
            'preserve_metadata': self.chk_preserve_meta.isChecked(),
            'preserve_cover': self.chk_preserve_cover.isChecked(),
            'rename_files': self.chk_rename.isChecked(),
            'delete_original': self.chk_delete_original.isChecked(),
            'reupload': self.chk_reupload.isChecked(),
            'extra_track_path': self.extra_track_path if self.method_merge.isChecked() else ""
        }

        # Сохранение в конфиг
        self.config_manager.set('pitch_value', settings['pitch_value'])
        self.config_manager.set('silence_duration', settings['silence_duration'])
        self.config_manager.set('speed_value', settings['speed_value'])
        self.config_manager.set('eq_value', settings['eq_value'])
        self.config_manager.set('quality', settings['quality'])
        self.config_manager.set('preserve_metadata', settings['preserve_metadata'])
        self.config_manager.set('preserve_cover', settings['preserve_cover'])
        self.config_manager.save()

        return settings

    def _start_modification(self):
        """Запуск обработки"""
        if not self.input_files:
            QMessageBox.warning(self, "Внимание", "Добавьте файлы для обработки!")
            return

        if not self.output_dir:
            reply = QMessageBox.question(
                self, "Папка не выбрана",
                "Использовать папку исходных файлов для сохранения?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.output_dir = os.path.dirname(self.input_files[0])
            else:
                return

        os.makedirs(self.output_dir, exist_ok=True)
        settings = self._get_settings()

        if settings['methods']['merge'] and not settings['extra_track_path']:
            QMessageBox.warning(self, "Внимание", "Выбран метод сращивания, но не выбран трек!")
            return

        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.input_files))
        self.progress_bar.setValue(0)

        self.worker = ModificationWorker(
            self.input_files,
            self.tracks_info,
            self.output_dir,
            settings,
            {
                'title': self.edit_title.text(),
                'artist': self.edit_artist.text(),
                'album': self.edit_album.text(),
                'year': self.edit_year.text(),
                'genre': self.edit_genre.text()
            }
        )
        self.worker.progress_update.connect(self._update_progress)
        self.worker.file_complete.connect(self._on_file_complete)
        self.worker.all_complete.connect(self._on_all_complete)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _set_ui_enabled(self, enabled: bool):
        """Включение/выключение UI элементов"""
        self.btn_add.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled and self.file_list.count() > 0)
        self.btn_clear.setEnabled(enabled)
        self.btn_start.setEnabled(enabled)
        self.btn_output.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

    def _update_progress(self, current: int, total: int, file_name: str):
        """Обновление прогресса"""
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(
            f"Обработка {current}/{total}: {os.path.basename(file_name)}"
        )

    def _on_file_complete(self, file_name: str, success: bool, output_path: str):
        """Обработка завершения обработки файла"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if file_name in item.text():
                if success:
                    item.setText(f"[OK] {os.path.basename(file_name)}")
                else:
                    item.setText(f"[ERR] {os.path.basename(file_name)}")
                break

    def _on_all_complete(self, success_count: int, total_count: int):
        """Обработка завершения всех файлов"""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)

        if success_count == total_count:
            QMessageBox.information(
                self, "Готово",
                f"Все {total_count} треков успешно обработаны!\\n\\n"
                f"Сохранено в:\\n{self.output_dir}"
            )
        else:
            QMessageBox.warning(
                self, "Обработка завершена",
                f"Успешно: {success_count} из {total_count}\\n"
                f"Ошибок: {total_count - success_count}"
            )

        try:
            if sys.platform == 'win32':
                os.startfile(self.output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.output_dir])
            else:
                subprocess.run(['xdg-open', self.output_dir])
        except Exception:
            pass

    def _on_error(self, error_msg: str):
        """Обработка ошибки"""
        QMessageBox.critical(self, "Ошибка", error_msg)

'''
    
    # Чтение основного файла
    with open(main_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Поиск места для вставки (перед функцией main)
    main_func_marker = "\ndef main():"
    if main_func_marker in content:
        parts = content.split(main_func_marker)
        # Вставляем код перед main
        new_content = parts[0] + event_handlers_code + main_func_marker + parts[1]
        
        with open(main_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    
    return False


if __name__ == '__main__':
    # Этот скрипт используется для добавления методов в главный файл
    import sys
    if len(sys.argv) > 1:
        main_file = sys.argv[1]
        if add_event_handlers_to_main(main_file):
            print(f"Successfully added event handlers to {main_file}")
        else:
            print(f"Failed to add event handlers to {main_file}")
    else:
        print("Usage: python event_handlers.py <main_file_path>")
