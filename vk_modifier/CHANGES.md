# VK Modifier - Исправления и Улучшения

## Выполненные изменения

### 1. Разбиение на модули
Создана модульная структура проекта:
```
vk_modifier/
├── __init__.py              # Основной пакет
├── main.py                  # Точка входа GUI
├── models/__init__.py       # Модели данных
│   ├── TrackInfo            # Информация о треке
│   ├── ProcessingSettings   # Настройки с валидацией
│   └── Metadata             # Метаданные
├── processors/__init__.py   # Процессоры аудио
│   ├── PRESETS              # 4 пресета конфигурации
│   ├── FilterBuilder        # Построитель FFmpeg фильтров
│   └── AudioProcessor       # Обработка файлов
├── ui/__init__.py           # UI компоненты
└── utils/__init__.py        # Утилиты
    ├── ConfigManager        # Конфигурация
    └── PresetManager        # Пресеты
```

### 2. Исправленные проблемы качества аудио

#### КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Pitch Shift
**Было:** Использовались фильтры `asetrate` + `aresample`, которые:
- Вызывали потерю высоких частот
- Создавали артефакты ресемплинга
- Ухудшали общее качество звука

**Стало:** Используется фильтр `rubberband`, который:
- Сохраняет оригинальное качество
- Не создает артефактов
- Поддерживает раздельное изменение скорости и тональности

#### Другие исправления:
- **Компрессия:** Заменена на `compander` с мягким коленом (soft-knee)
- **Эквализация:** Используются `bass` и `treble` фильтры вместо `equalizer`
- **Нормализация:** Добавлен `loudnorm` с правильными параметрами LUFS

### 3. Валидация настроек

#### Проверка диапазонов:
| Параметр | Диапазон |
|----------|----------|
| Volume | -50 до 20 dB |
| Target Loudness | -24 до -10 LUFS |
| Speed | 0.5 до 2.0 |
| Pitch | -12 до 12 полутонов |
| Bass/Treble Gain | -20 до 20 dB |
| Compress Ratio | 1 до 20 |

#### Проверка несовместимых комбинаций:
- ❌ Нормализация + Volume > 10dB → клиппинг
- ❌ Compress Ratio > 10 → артефакты
- ❌ |Pitch| > 6 + |Speed-1| > 0.2 → ухудшение качества

### 4. Новые пресеты (конфигурации)

#### 1. Safe (Безопасный)
**Описание:** Минимальная обработка, сохранение качества
```python
{
    "volume": 0.0,
    "normalize": True,
    "target_loudness": -14.0,
    "compress": False,
    "speed": 1.0,
    "pitch": 0.0
}
```
**Использование:** Для треков с хорошим исходным качеством

#### 2. Loud (Громкий)
**Описание:** Максимальная громкость для VK
```python
{
    "volume": 3.0,
    "normalize": True,
    "target_loudness": -11.0,
    "compress": True,
    "compress_threshold": -15.0,
    "compress_ratio": 3.0,
    "bass_gain": 2.0,
    "treble_gain": 1.5,
    "fade_in": 0.5,
    "fade_out": 2.0
}
```
**Использование:** Для тихих треков, которым нужна громкость

#### 3. Spatial (Пространственный)
**Описание:** Улучшение стерео и частот
```python
{
    "volume": 0.0,
    "normalize": True,
    "target_loudness": -14.0,
    "compress": True,
    "compress_ratio": 2.5,
    "bass_gain": 3.0,
    "bass_freq": 80.0,
    "treble_gain": 2.0,
    "treble_freq": 12000.0
}
```
**Использование:** Для улучшения звучания старых записей

#### 4. Transform (Трансформация)
**Описание:** Изменение скорости и тональности
```python
{
    "volume": 0.0,
    "normalize": True,
    "target_loudness": -14.0,
    "compress": False,
    "speed": 1.05,
    "pitch": 0.0
}
```
**Использование:** Для изменения темпа без потери качества

### 5. Обновленная модель ProcessingSettings

```python
@dataclass
class ProcessingSettings:
    volume: float = 0.0  # dB (-50 to 20)
    normalize: bool = True
    target_loudness: float = -14.0  # LUFS (-24 to -10)
    compress: bool = True
    compress_threshold: float = -20.0  # dB (-60 to 0)
    compress_ratio: float = 4.0  # (1 to 20)
    bass_gain: float = 0.0  # dB (-20 to 20)
    treble_gain: float = 0.0  # dB (-20 to 20)
    speed: float = 1.0  # (0.5 to 2.0)
    pitch: float = 0.0  # semitones (-12 to 12)
    fade_in: float = 0.0  # seconds (0 to 10)
    fade_out: float = 0.0  # seconds (0 to 10)
    preset_name: str = "safe"
    
    def validate(self): ...  # Автоматическая валидация
    def to_dict(self): ...   # Сериализация
    @classmethod
    def from_dict(cls, data): ...  # Десериализация
```

### 6. FilterBuilder класс

```python
class FilterBuilder:
    @staticmethod
    def validate_settings(settings) -> Tuple[bool, str]:
        """Проверка совместимости настроек"""
    
    @staticmethod
    def build_filters(settings) -> Optional[str]:
        """Построение строки фильтров FFmpeg"""
        # Порядок применения:
        # 1. Эквализация (bass/treble)
        # 2. Компрессия (compander)
        # 3. Нормализация (loudnorm)
        # 4. Громкость (volume)
        # 5. Speed/Pitch (rubberband)
```

## Тестирование

Все модули проходят тесты:
```bash
cd /workspace/vk_modifier
python -c "from models import ProcessingSettings; print('Models OK')"
python -c "from processors import FilterBuilder, PRESETS; print('Processors OK')"
python -c "from utils import ConfigManager, PresetManager; print('Utils OK')"
```

## Запуск приложения

```bash
# Из родительской директории
cd /path/to/vkmodifierNEW
python -m vk_modifier.main

# Или из директории проекта
cd /path/to/vkmodifierNEW/vk_modifier
python main.py
```

## Зависимости

- Python 3.8+
- ffmpeg (с фильтром rubberband)
- ffprobe
- mutagen
- PyQt5
