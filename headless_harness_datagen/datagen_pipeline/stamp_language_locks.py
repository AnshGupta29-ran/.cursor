"""Ensure every forged platform_prompt.md starts with an explicit language lock banner."""

from __future__ import annotations

import json
import re
from pathlib import Path

from datagen_pipeline.paths import BANK

BANNER_RE = re.compile(r"^## LANGUAGE LOCK \(datagen\)\n", re.M)


def stamp_one(prompt: Path, language: str, ui: str, persistence: str, complexity: str) -> bool:
    text = prompt.read_text(encoding="utf-8")
    banner = (
        f"## LANGUAGE LOCK (datagen)\n"
        f"- **language_runtime (MANDATORY):** `{language}`\n"
        f"- **ui_surface:** `{ui}`\n"
        f"- **persistence:** `{persistence}`\n"
        f"- **complexity:** `{complexity}`\n"
        f"- Do **not** rewrite this project in a different language.\n\n"
    )
    if BANNER_RE.search(text):
        # replace existing banner block (until blank line after complexity or next ##)
        text2 = re.sub(
            r"## LANGUAGE LOCK \(datagen\)\n(?:.*\n)*?(?=\n## |\n# |\Z)",
            banner.rstrip() + "\n\n",
            text,
            count=1,
        )
        if text2 != text:
            prompt.write_text(text2, encoding="utf-8")
            return True
        return False
    # Insert after first H1 block / at top after first heading section
    if text.startswith("#"):
        # after first paragraph block
        parts = text.split("\n\n", 1)
        if len(parts) == 2:
            text = parts[0] + "\n\n" + banner + parts[1]
        else:
            text = banner + text
    else:
        text = banner + text
    prompt.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    n = 0
    for cat_dir in sorted(p for p in BANK.iterdir() if p.is_dir()):
        for seed_path in cat_dir.glob("*.json"):
            try:
                seed = json.loads(seed_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            idx = int(seed.get("index") or 0)
            hint = seed.get("dimensions_hint") or {}
            forged = list((cat_dir / "forged").glob(f"{idx:02d}_*/platform_prompt.md"))
            if not forged:
                continue
            if stamp_one(
                forged[0],
                str(hint.get("language_runtime") or "python"),
                str(hint.get("ui_surface") or "static_html"),
                str(hint.get("persistence") or "sqlite"),
                str(hint.get("complexity") or "medium"),
            ):
                n += 1
                print(f"stamped {cat_dir.name}:{idx:02d} -> {hint.get('language_runtime')}")
    print(f"updated {n} prompts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
