import pygame

_sound: pygame.mixer.Sound | None = None
_available = False


def init(mp3_path: str) -> bool:
    global _sound, _available
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
        pygame.mixer.init()
        _sound = pygame.mixer.Sound(mp3_path)
        _available = True
        return True
    except Exception:
        _available = False
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        return False


def play(volume: float = 1.0) -> None:
    if _available and _sound is not None:
        _sound.set_volume(max(0.0, min(1.0, volume)))
        _sound.play()


def cleanup() -> None:
    global _available
    if _available:
        pygame.mixer.quit()
        _available = False
