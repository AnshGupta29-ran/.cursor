# save.py
"""Stasis save/restore utilities.
Creates a deep copy snapshot of the full game state and can restore it.
"""
import copy

def snapshot(game) -> dict:
    """Capture a full snapshot of the current game state.
    Returns a plain dict that can be serialized if needed.
    """
    return {
        "seed": game.seed,
        "prng_state": game.prng_state,
        "turn_count": game.turn_count,
        "flare_timer": game.flare_timer,
        "player": copy.deepcopy(game.player),
        "dungeon": copy.deepcopy(game.dungeon),
        "entities": copy.deepcopy(game.entities),
        "inventory": copy.deepcopy(game.inventory),
        "game_over": game.game_over,
        "victory": game.victory,
    }

def restore(game, state: dict):
    """Restore the game from a snapshot dict.
    Mutates the provided game instance in‑place.
    """
    game.seed = state["seed"]
    game.prng_state = state["prng_state"]
    game.turn_count = state["turn_count"]
    game.flare_timer = state["flare_timer"]
    game.player = copy.deepcopy(state["player"])
    game.dungeon = copy.deepcopy(state["dungeon"])
    game.entities = copy.deepcopy(state["entities"])
    game.inventory = copy.deepcopy(state["inventory"])
    game.game_over = state["game_over"]
    game.victory = state["victory"]
    # Re‑initialize UI reference which may not survive deepcopy
    # Assume UI uses the same screen/fonts which are unchanged
    # No need to recreate UI instance; it remains attached to game
