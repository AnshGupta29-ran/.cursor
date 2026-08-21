"""CLI helper for audittrail demo.
Provides simple commands to interact with the AuditStore without a server.
"""

import argparse
import sys
from pathlib import Path

from audittrail.store import AuditStore


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="audittrail-cli", description="Audit trail CLI for EpochLedger demo")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # submit event
    sub = subparsers.add_parser("submit", help="Submit a new audit event")
    sub.add_argument("event_type", help="Type of event (e.g., login, model_train)")
    sub.add_argument("user", help="User performing the event")
    sub.add_argument("description", help="Human‑readable description")

    # list events
    subparsers.add_parser("list", help="List all events")

    # export signed csv
    sub = subparsers.add_parser("export", help="Export signed audit trail CSV")
    sub.add_argument("output", nargs="?", default="audit_trail.csv", help="Output CSV file path")

    # verify signature
    sub = subparsers.add_parser("verify", help="Verify CSV signature")
    sub.add_argument("csv_path", help="Path to CSV file to verify")

    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv or sys.argv[1:])
    store = AuditStore()

    if args.cmd == "submit":
        ev = store.add_event(args.event_type, args.user, args.description)
        print(f"Added event {ev['id']}: {ev['event_type']} by {ev['user']}")
    elif args.cmd == "list":
        for ev in store.list_events():
            print(ev)
    elif args.cmd == "export":
        path = store.export_signed(args.output)
        print(f"Exported signed audit trail to {path}")
    elif args.cmd == "verify":
        ok = store.verify_signature(args.csv_path)
        print("Signature VALID" if ok else "Signature INVALID")
        sys.exit(0 if ok else 1)
    else:
        raise RuntimeError("unknown command")

if __name__ == "__main__":
    main()
