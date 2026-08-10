import os, sys, time, threading
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
game_dir = sys.argv[1]
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
os.chdir(game_dir)
sys.path.insert(0, game_dir)
import pygame
pygame.init()
def _quit_soon():
    time.sleep(seconds)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass
    time.sleep(1.0)
    os._exit(0)
threading.Thread(target=_quit_soon, daemon=True).start()
path = os.path.join(game_dir, "main.py")
code = open(path, encoding="utf-8").read()
exec(compile(code, path, "exec"), {"__name__": "__main__", "__file__": path})
print("SMOKE_OK", game_dir)
