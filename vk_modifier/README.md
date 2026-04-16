# VK Track Modifier - Модульная версия

Приложение для обработки MP3 треков с целью обхода алгоритмов контент-матчинга VK.

## Структура проекта

```
vk_modifier/
├── __init__.py          # Основной пакет
├── main.py              # Точка входа GUI приложения
├── README.md            # Документация
├── models/              # Модели данных
│   └── __init__.py      # TrackInfo, ProcessingSettings, Metadata
├── processors/          # Процессоры обработки аудио
│   └── __init__.py      # FilterBuilder, AudioProcessor
├── ui/                  # UI компоненты
│   ├── __init__.py      # CoverPreviewLabel, CollapsibleGroup
│   └── event_handlers.py # Обработчики событий
└── utils/               # Утилиты
    └── __init__.py      # ConfigManager, MetadataExtractor, PresetManager
```

## Модули

### models
- **TrackInfo**: Класс для хранения информации о треке (путь, размер, метаданные, обложка)
- **ProcessingSettings**: Настройки обработки с методами конвертации в/from dict
- **Metadata**: Метаданные трека (название, исполнитель, альбом, год, жанр)

### processors
- **FilterBuilder**: Построитель FFmpeg аудио фильтров
  - Pitch shift (изменение тональности)
  - Tempo change (изменение скорости)
  - Equalizer (эквализация)
  - Phaser (фазовый сдвиг)
  - Noise addition (добавление шума)
  - Compression (компрессия)
  - Silence padding (добавление тишины)

- **AudioProcessor**: Основной процессор аудио
  - Обрезка тишины
  - Вырезание фрагментов
  - Сращивание треков
  - Применение фильтров
  - Модификация ID3 тегов
  - Broken duration (для сбоя парсинга)

### ui
- **CoverPreviewLabel**: Кастомный QLabel для предпросмотра обложки
- **CollapsibleGroup**: Сворачиваемая группа QGroupBox
- **event_handlers.py**: Все обработчики событий для главного окна

### utils
- **ConfigManager**: Управление конфигурацией (загрузка/сохранение JSON)
- **MetadataExtractor**: Извлечение метаданных и обложек из MP3
- **PresetManager**: Управление пресетами обработки (enhanced, reupload)
- **check_ffmpeg**: Проверка доступности FFmpeg
- Helper функции для значений параметров

## Установка зависимостей

```bash
pip install PyQt5 mutagen
```

Также требуется установленный FFmpeg:
- Linux: `apt install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: скачать с ffmpeg.org

## Запуск

```bash
cd vk_modifier
python main.py
```

## Исправленные проблемы оригинального кода

1. **Модульная структура**: Код разбит на логические модули
2. **Data classes**: Использование dataclasses для моделей данных
3. **Типизация**: Добавлены type hints для лучшей читаемости
4. **DRY принцип**: Убрано дублирование кода (FilterBuilder используется в обоих местах)
5. **Конфигурация**: Выделен отдельный ConfigManager класс
6. **Пресеты**: Пресеты вынесены в PresetManager с централизованным управлением
7. **Обработка ошибок**: Улучшена обработка исключений
8. **Валидация параметров**: Добавлена проверка диапазонов для atempo (0.5-2.0)
9. **Очистка ресурсов**: Гарантированная очистка временных файлов

## Новые возможности

1. **ProcessingSettings.to_dict()/from_dict()**: Конвертация настроек
2. **Metadata dataclass**: Удобная работа с метаданными
3. **Централизованные константы**: get_pitch_values(), get_speed_values() и т.д.
4. **Расширенная документация**: Docstrings для всех классов и методов

## Лицензия

Использовать ответственно и в соответствии с законодательством.
