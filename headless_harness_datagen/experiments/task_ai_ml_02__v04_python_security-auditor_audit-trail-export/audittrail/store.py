"""audittrail.store
Simple JSON‑based audit‑trail store for the EpochLedger demo.
"""

import json
import os
import time
import csv
import hmac
import hashlib
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STORE_FILE = DATA_DIR / "audit_log.json"

# Hard‑coded secret for HMAC signing (demo only).
_HMAC_KEY = b"demo-secret-key"


def _current_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


class AuditStore:
    """Manage a list of audit events persisted as JSON.

    Each event is a dict with the keys:
        - id: int (incremental)
        - timestamp: ISO‑8601 UTC string
        - event_type: str
        - user: str
        - description: str
    """

    def __init__(self, file_path: Path | str = STORE_FILE):
        self.file_path = Path(file_path)
        self._ensure_file()
        self._load()

    def _ensure_file(self) -> None:
        if not self.file_path.exists():
            # Initialise with empty list
            self.file_path.write_text(json.dumps([]))

    def _load(self) -> None:
        try:
            self.events: List[Dict[str, Any]] = json.loads(self.file_path.read_text())
        except Exception:
            self.events = []

    def _save(self) -> None:
        self.file_path.write_text(json.dumps(self.events, indent=2))

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def add_event(self, event_type: str, user: str, description: str) -> Dict[str, Any]:
        event_id = (self.events[-1]["id"] + 1) if self.events else 1
        ev = {
            "id": event_id,
            "timestamp": _current_ts(),
            "event_type": event_type,
            "user": user,
            "description": description,
        }
        self.events.append(ev)
        self._save()
        return ev

    def list_events(self) -> List[Dict[str, Any]]:
        return list(self.events)

    def export_csv(self, output_path: Path | str) -> Path:
        output_path = Path(output_path)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "timestamp", "event_type", "user", "description"])
            writer.writeheader()
            for ev in self.events:
                writer.writerow(ev)
        return output_path

    def export_signed(self, output_path: Path | str) -> Path:
        """Export CSV and append an HMAC‑SHA256 signature line.

        The signature covers the raw CSV bytes (excluding the signature line).
        """
        csv_path = self.export_csv(output_path)
        data = csv_path.read_bytes()
        sig = hmac.new(_HMAC_KEY, data, hashlib.sha256).hexdigest()
        # Append a comment line with the signature – CSV readers will ignore it.
        with csv_path.open("a", encoding="utf-8") as f:
            f.write(f"#signature:{sig}\n")
        return csv_path

    def verify_signature(self, csv_path: Path | str) -> bool:
        csv_path = Path(csv_path)
        lines = csv_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return False
        # The last line should be the signature comment.
        sig_line = lines[-1]
        if not sig_line.startswith("#signature:"):
            return False
        expected = sig_line.split(":", 1)[1].strip()
        raw = "\n".join(lines[:-1]).encode("utf-8") + b"\n"
        actual = hmac.new(_HMAC_KEY, raw, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, actual)
