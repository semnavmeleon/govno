"""Единый сборщик цепочки ffmpeg-фильтров.

Объединяет build_filters + build_filter_complex.
Правильный порядок: trim → pitch/speed → eq → phase → compression → dc_shift → fade → silence.
Noise/ultrasound через filter_complex (требуют генерацию источников).
"""

import random
import logging

logger = logging.getLogger('vk_modifier.filters')


class FilterChain:
    """Строит цепочку фильтров для ffmpeg."""

    def __init__(self, settings: dict, duration: float = 300.0):
        self.s = settings
        self.duration = duration

    def build(self) -> tuple[list[str], str | None, str | None]:
        """
        Возвращает (extra_args, filter_str_or_none, map_label_or_none).

        Если нужен -filter_complex → возвращает ([], fc_string, "[out]")
        Если нужен только -af      → возвращает ([], af_string, None)
        Если нет фильтров           → возвращает ([], None, None)
        """
        simple = self._build_simple_filters()
        needs_complex = self._needs_filter_complex()

        if needs_complex:
            fc, label = self._build_filter_complex(simple)
            return [], fc, label
        elif simple:
            return [], ",".join(simple), None
        else:
            return [], None, None

    def _build_simple_filters(self) -> list[str]:
        """Собрать простые аудиофильтры в правильном порядке."""
        f = []

        # 1. Pitch
        pitch = self.s.get('pitch_semitones', 0.0)
        if pitch != 0.0:
            rate = 44100 * (2 ** (pitch / 12))
            f.append(f"asetrate={rate:.0f},aresample=44100")

        # 2. Speed
        speed = self.s.get('speed_factor', 1.0)
        if speed != 1.0:
            f.append(f"atempo={speed}")

        # 3. EQ
        eq_idx = self.s.get('eq_preset_index', -1)
        if eq_idx >= 0:
            from ..constants import EQ_PRESETS
            if eq_idx < len(EQ_PRESETS):
                _, eq_filter = EQ_PRESETS[eq_idx]
                f.append(eq_filter)

        # 4. Phase
        phase = self.s.get('phase_delay_ms', 0.0)
        if phase > 0:
            f.append(f"aphaser=type=t:delay={phase}:decay=0.4:speed=0.5")

        # 5. Compression
        if self.s.get('compression_enabled'):
            f.append("compand=attacks=0.1:decays=0.1:points=-80/-80|-45/-15|-27/-9|0/-7|20/-7")

        # 6. DC Shift
        if self.s.get('dc_shift_enabled'):
            f.append("dcshift=0.001")

        # 7. Fade in (ПЕРЕД silence)
        fade_in = self.s.get('fade_in_sec', 0)
        if fade_in > 0:
            f.append(f"afade=t=in:st=0:d={fade_in}")

        # 8. Fade out (ПЕРЕД silence, от конца МУЗЫКИ)
        fade_out = self.s.get('fade_out_sec', 0)
        if fade_out > 0 and self.duration > 0:
            start = max(0, self.duration - fade_out)
            f.append(f"afade=t=out:st={start:.1f}:d={fade_out}")

        # 9. Silence (ПОСЛЕ fade)
        silence = self.s.get('silence_end_sec', 0)
        if silence > 0:
            f.append(f"apad=pad_dur={silence}")

        return f

    def _needs_filter_complex(self) -> bool:
        """Нужен ли -filter_complex (noise/ultrasound требуют генерацию источников)."""
        return (
            self.s.get('noise_amplitude', 0.0) > 0
            or self.s.get('ultrasound_enabled', False)
        )

    def _build_filter_complex(self, simple_filters: list[str]) -> tuple[str, str]:
        """Собрать -filter_complex с noise/ultrasound источниками."""
        dur = max(self.duration + 60, 600)
        parts = []
        labels = ["[main]"]
        n = 1

        # Основной поток
        if simple_filters:
            parts.append(f"[0:a]{','.join(simple_filters)}[main]")
        else:
            parts.append("[0:a]acopy[main]")

        # Розовый шум
        noise_amp = self.s.get('noise_amplitude', 0.0)
        if noise_amp > 0:
            parts.append(f"anoisesrc=d={dur}:c=pink:a={noise_amp}[noise]")
            labels.append("[noise]")
            n += 1

        # Ультразвук
        if self.s.get('ultrasound_enabled'):
            freq = random.choice([19500, 20000, 20500, 21000])
            parts.append(f"sine=frequency={freq}:duration={dur}:sample_rate=44100,volume=0.003[ultra]")
            labels.append("[ultra]")
            n += 1

        # Микширование
        parts.append(f"{''.join(labels)}amix=inputs={n}:duration=first:dropout_transition=0[out]")
        return ";".join(parts), "[out]"


def get_codec_args(settings: dict) -> list[str]:
    """Аргументы кодека для финального кодирования."""
    args = ['-codec:a', 'libmp3lame']

    if settings.get('bitrate_jitter'):
        br = random.choice([192, 224, 256, 320])
        args.extend(['-b:a', f'{br}k'])
    else:
        quality = settings.get('quality', '2')
        args.extend(['-q:a', quality])

    if settings.get('frame_shift') and not settings.get('broken_duration_enabled'):
        args.extend(['-write_xing', '0'])

    args.extend(['-id3v2_version', '3'])
    return args
