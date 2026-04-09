import math
import struct
import wave
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SOUND_DIR = ROOT_DIR / "angels_and_demons_game" / "assets" / "sounds"
SAMPLE_RATE = 44100


def envelope(sample_index, total_samples, attack=0.08, release=0.22):
    progress = sample_index / max(1, total_samples - 1)
    if progress < attack:
        return progress / max(attack, 1e-6)
    if progress > 1.0 - release:
        return max(0.0, (1.0 - progress) / max(release, 1e-6))
    return 1.0


def build_tone(frequencies, duration_s, volume=0.45, vibrato=0.0, sweep=0.0):
    total_samples = int(SAMPLE_RATE * duration_s)
    frames = []
    for index in range(total_samples):
        time_point = index / SAMPLE_RATE
        env = envelope(index, total_samples)
        sample = 0.0
        for frequency in frequencies:
            current_frequency = frequency + math.sin(time_point * 11.0) * vibrato + sweep * (index / max(1, total_samples))
            sample += math.sin(2.0 * math.pi * current_frequency * time_point)
        sample /= max(1, len(frequencies))
        sample *= env * volume
        frames.append(int(max(-1.0, min(1.0, sample)) * 32767))
    return frames


def save_wav(filename, frames):
    SOUND_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SOUND_DIR / filename
    with wave.open(str(filepath), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(b"".join(struct.pack("<h", frame) for frame in frames))


def save_outputs():
    save_wav("ui_click.wav", build_tone([940, 1260], 0.10, volume=0.22))
    save_wav("box_flip.wav", build_tone([540, 760], 0.13, volume=0.28, sweep=-140))
    save_wav("point_gain.wav", build_tone([660, 880, 1180], 0.18, volume=0.24, sweep=120))
    save_wav("point_loss.wav", build_tone([540, 420], 0.22, volume=0.26, sweep=-180))
    save_wav("achievement.wav", build_tone([660, 880, 1320], 0.42, volume=0.26, vibrato=5))
    save_wav("bot_move.wav", build_tone([480, 620], 0.16, volume=0.20, sweep=60))


if __name__ == "__main__":
    save_outputs()
    print("sound fx generated")
