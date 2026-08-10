#!/usr/bin/env python3
"""Deepvault Survey Roguelike
A small offline‑first ASCII roguelike rendered with pygame.
"""

import sys
import pygame
from game import Game

pygame.init()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal error: {exc}")
        sys.exit(1)
