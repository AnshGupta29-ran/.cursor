import argparse
import sys
import uuid
from pathlib import Path
from . import parse_csv, detect, plot, export_report, DATA_DIR

def main():
    parser = argparse.ArgumentParser(prog='hivepulse', description='HivePulse – offline anomaly flagger for beekeepers')
    parser.add_argument('csv', nargs='?', help='Path to CSV file with timestamp and metric columns')
    parser.add_argument('--detector', choices=['zscore', 'iqr'], default='zscore', help='Detection algorithm')
    parser.add_argument('--threshold', type=float, default=2.0, help='Threshold for detector (zscore value or IQR multiplier)')
    parser.add_argument('--preset', default='default', help='Preset name for this run')
    parser.add_argument('--plot', action='store_true', help='Render an ASCII plot of the series with anomalies')
    parser.add_argument('--export', metavar='PATH', help='Export JSON report to given file')
    parser.add_argument('--history', action='store_true', help='Print past runs summary')

    args = parser.parse_args()

    if args.history:
        hist_path = DATA_DIR / 'history.json'
        if not hist_path.exists():
            print('No history file found.')
            return
        import json
        with open(hist_path, 'r', encoding='utf-8') as f:
            hist = json.load(f)
        for entry in hist:
            print(f"Run {entry.get('run_id')} – {entry.get('detector')} – {entry.get('window_count')} windows – {entry.get('timestamp')}")
        return

    if not args.csv:
        parser.print_help()
        sys.exit(1)

    try:
        series = parse_csv(args.csv)
    except Exception as e:
        print(f'Error parsing CSV: {e}')
        sys.exit(1)

    windows = detect(series, args.detector, args.threshold)

    print(f'Ingested {series.metadata["row_count"]} rows (rejected {series.metadata["rejected_rows"]})')
    print(f'Detected {len(windows)} anomaly window(s) using {args.detector}')
    for w in windows:
        print(f" - {w.start} to {w.end} ({w.direction}, score={w.peak_score:.2f})")

    if args.plot:
        print('\nASCII plot (anomalies marked with "*")')
        plot(series, windows)

    if args.export:
        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        run_id = str(uuid.uuid4())
        export_report(run_id, args.csv, args.detector, args.threshold, args.preset, windows, str(export_path))
        print(f'Exported report to {export_path}')

if __name__ == '__main__':
    main()
