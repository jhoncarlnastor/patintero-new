
import math
import random
import struct
import pygame


# ==========================================
# PATINTERO: GRID RUSH — PROCEDURAL AUDIO
# No external sound files required
# ==========================================

SAMPLE_RATE = 22050

_muted = False
_volume = 0.45
_sounds = {}
_audio_ready = False


def init_audio():
    """Initialize the audio system and generate sound effects."""
    global _audio_ready, _sounds

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(
                frequency=SAMPLE_RATE,
                size=-16,
                channels=1,
                buffer=512,
            )

        _sounds = {
            "star": _make_tone(
                start_freq=880,
                end_freq=1320,
                duration=0.16,
                volume=0.55,
                waveform="sine",
            ),
            "hit": _make_tone(
                start_freq=220,
                end_freq=95,
                duration=0.28,
                volume=0.65,
                waveform="square",
            ),
            "victory": _make_melody(
                [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.28)]
            ),
            "game_over": _make_melody(
                [(392, 0.18), (330, 0.18), (262, 0.32)]
            ),
            "click": _make_tone(
                start_freq=650,
                end_freq=820,
                duration=0.055,
                volume=0.3,
                waveform="sine",
            ),
            "pickup": _make_tone(
                start_freq=600,
                end_freq=900,
                duration=0.12,
                volume=0.5,
                waveform="sine",
            ),
            "coin": _make_melody([(1047, 0.07), (1568, 0.16)]),
            "heart": _make_melody([(523, 0.08), (659, 0.08), (784, 0.14)]),
            "shield": _make_tone(
                start_freq=300,
                end_freq=700,
                duration=0.2,
                volume=0.5,
                waveform="square",
            ),
            "shield_break": _make_tone(
                start_freq=700,
                end_freq=200,
                duration=0.22,
                volume=0.5,
                waveform="square",
            ),
            "dash": _make_tone(
                start_freq=400,
                end_freq=1000,
                duration=0.1,
                volume=0.4,
                waveform="sine",
            ),
            "unlock": _make_melody(
                [(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.1), (1319, 0.3)]
            ),
            "buy": _make_melody([(784, 0.08), (988, 0.08), (1319, 0.2)]),
            "denied": _make_tone(
                start_freq=180,
                end_freq=140,
                duration=0.15,
                volume=0.5,
                waveform="square",
            ),
        }

        _audio_ready = True
        _apply_volume()

    except (pygame.error, OSError):
        # The game can still run if audio is unavailable.
        _audio_ready = False
        _sounds = {}


def _make_tone(
    start_freq,
    end_freq,
    duration,
    volume=0.5,
    waveform="sine",
):
    """Create a short sound by generating raw PCM audio."""
    sample_count = int(SAMPLE_RATE * duration)
    samples = bytearray()

    for i in range(sample_count):
        t = i / SAMPLE_RATE
        progress = i / max(1, sample_count - 1)
        frequency = start_freq + (end_freq - start_freq) * progress

        phase = 2 * math.pi * frequency * t

        if waveform == "square":
            wave = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            wave = math.sin(phase)

        # Fade in/out to reduce clicking and harsh sound endings.
        fade_in = min(1.0, t / 0.012)
        fade_out = min(1.0, (duration - t) / 0.035)
        envelope = max(0.0, min(fade_in, fade_out))

        sample = int(
            32767 * volume * envelope * wave
        )
        samples.extend(struct.pack("<h", sample))

    return pygame.mixer.Sound(buffer=bytes(samples))


def _make_melody(notes):
    """Create a simple sequence of notes in one sound."""
    pieces = bytearray()

    for frequency, duration in notes:
        count = int(SAMPLE_RATE * duration)

        for i in range(count):
            t = i / SAMPLE_RATE
            fade_in = min(1.0, t / 0.01)
            fade_out = min(1.0, (duration - t) / 0.035)
            envelope = max(0.0, min(fade_in, fade_out))

            wave = math.sin(2 * math.pi * frequency * t)
            sample = int(32767 * 0.48 * envelope * wave)
            pieces.extend(struct.pack("<h", sample))

        # Add a small silence between notes.
        pieces.extend(b"\x00\x00" * int(SAMPLE_RATE * 0.025))

    return pygame.mixer.Sound(buffer=bytes(pieces))


def _apply_volume():
    """Apply the current volume to every sound effect."""
    for sound in _sounds.values():
        sound.set_volume(0.0 if _muted else _volume)


def play_sound(name):
    """Play a sound by name: star, hit, victory, game_over, click."""
    if not _audio_ready or _muted:
        return

    sound = _sounds.get(name)

    if sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass


def set_volume(value):
    """Set volume from 0.0 (silent) to 1.0 (maximum)."""
    global _volume

    _volume = max(0.0, min(1.0, float(value)))
    _apply_volume()


def get_volume():
    return _volume


def toggle_mute():
    """Turn sound on or off. Returns the new mute state."""
    global _muted

    _muted = not _muted
    _apply_volume()
    return _muted


def is_muted():
    return _muted
