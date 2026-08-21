"""Simple CLI for EpochLedger.
Provides sub‑commands for basic operations. The demo uses the Python standard
library only (argparse + json)."""

import argparse
import json
import sys
from pathlib import Path

from .experiment import (
    create_experiment,
    start_run,
    log_metric,
    finish_run,
    set_champion,
    get_experiment_by_name,
    get_latest_metrics,
)
from .db import reset_db, init_db


def _parse_params(param_str: str):
    """Parse a JSON string of parameters passed on the CLI.
    Returns a dict or None.
    """
    if not param_str:
        return None
    try:
        return json.loads(param_str)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON for params: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='epochledger')
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('init-db', help='Create (or reset) the SQLite database')

    create_exp = sub.add_parser('create-experiment', help='Create a new experiment')
    create_exp.add_argument('name')

    start = sub.add_parser('start-run', help='Start a new run')
    start.add_argument('experiment_name')
    start.add_argument('run_name')
    start.add_argument('--params', help='JSON string of parameters')

    log = sub.add_parser('log-metric', help='Log a metric for a run')
    log.add_argument('run_id', type=int)
    log.add_argument('key')
    log.add_argument('value', type=float)

    sub.add_parser('finish-run', help='Mark a run as completed').add_argument('run_id', type=int)

    champ = sub.add_parser('set-champion', help='Promote a run to champion')
    champ.add_argument('experiment_name')
    champ.add_argument('run_id', type=int)

    args = parser.parse_args(argv)

    if args.command == 'init-db':
        reset_db()
        print('Database reset and initialised.')
    elif args.command == 'create-experiment':
        exp_id = create_experiment(args.name)
        print(f'Experiment created with id {exp_id}')
    elif args.command == 'start-run':
        exp = get_experiment_by_name(args.experiment_name)
        if not exp:
            print(f'Experiment {args.experiment_name!r} not found', file=sys.stderr)
            sys.exit(1)
        run_id = start_run(exp['id'], args.run_name, _parse_params(args.params))
        print(f'Run started with id {run_id}')
    elif args.command == 'log-metric':
        log_metric(args.run_id, args.key, args.value)
        print('Metric logged.')
    elif args.command == 'finish-run':
        finish_run(args.run_id)
        print('Run finished.')
    elif args.command == 'set-champion':
        exp = get_experiment_by_name(args.experiment_name)
        if not exp:
            print(f'Experiment {args.experiment_name!r} not found', file=sys.stderr)
            sys.exit(1)
        set_champion(exp['id'], args.run_id)
        print('Champion set.')
    else:
        parser.print_help()
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
