import argparse
import sys
import uuid
from pathlib import Path
from datetime import datetime
from . import parse_csv, detect, plot, export_report, DATA_DIR

def main():
    parser = argparse.ArgumentParser(prog='hivepulse', description='HivePulse – offline anomaly flagger for beekeepers')
    parser.add_argument('csv', nargs='?', help='Path to CSV file with timestamp and metric columns')
    parser.add_argument('--detector', choices=['zscore', 'iqr'], default='zscore', help='Detection algorithm')
    parser.add_argument('--threshold', type=float, default=1.5, help='Threshold for detector (zscore value or IQR multiplier)')
    parser.add_argument('--preset', default='default', help='Preset name for this run')
    parser.add_argument('--plot', action='store_true', help='Render an ASCII plot of the series with anomalies')
    parser.add_argument('--export', metavar='PATH', help='Export JSON report to given file')
    parser.add_argument('--history', action='store_true', help='Print past runs summary')
    parser.add_argument('--menu', action='store_true', help='Start interactive TUI menu')

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

    # Interactive menu mode
    if args.menu or not args.csv:
        series = None
        windows = []
        detector = 'zscore'
        threshold = 2.0
        preset = 'default'
        while True:
            print('\nHivePulse Menu:')
            print('1) Load CSV')
            print('2) Detect anomalies')
            print('3) Plot series')
            print('4) Compare detectors')
            print('5) Export report')
            print('6) Show history')
            print('7) Quit')
            choice = input('Select option: ').strip()
            if choice == '1':
                path = input('Enter CSV path: ').strip()
                try:
                    series = parse_csv(path)
                    print(f'Loaded {series.metadata["row_count"]} rows (rejected {series.metadata["rejected_rows"]})')
                except Exception as e:
                    print(f'Error loading CSV: {e}')
            elif choice == '2':
                if not series:
                    print('Load a CSV first.')
                    continue
                det = input(f'Enter detector [{detector}]: ').strip() or detector
                thr = input(f'Enter threshold [{threshold}]: ').strip()
                thr = float(thr) if thr else threshold
                windows = detect(series, det, thr)
                detector, threshold = det, thr
                print(f'Detected {len(windows)} anomaly window(s) using {detector}')
                for w in windows:
                    print(f" - {w.start} to {w.end} ({w.direction}, score={w.peak_score:.2f})")
            elif choice == '3':
                if not series:
                    print('Load a CSV first.')
                    continue
                if not windows:
                    print('Run detection first.')
                    continue
                print('\nASCII plot (anomalies marked with "*")')
                plot(series, windows)
            elif choice == '4':
                if not series:
                    print('Load a CSV first.')
                    continue
                z_windows = detect(series, 'zscore', 2.0)
                iqr_windows = detect(series, 'iqr', 1.5)
                print(f'Z-score windows: {len(z_windows)}')
                print(f'IQR windows: {len(iqr_windows)}')
                # simple overlap count
                overlap = 0
                for zw in z_windows:
                    zs = datetime.fromisoformat(zw.start)
                    ze = datetime.fromisoformat(zw.end)
                    for iw in iqr_windows:
                        is_ = datetime.fromisoformat(iw.start)
                        ie = datetime.fromisoformat(iw.end)
                        if max(zs, is_) <= min(ze, ie):
                            overlap += 1
                            break
                print(f'Overlap windows: {overlap}')
            elif choice == '5':
                if not windows:
                    print('Run detection first.')
                    continue
                out_path = input('Export path (default report.json): ').strip() or 'report.json'
                export_path = Path(out_path)
                export_path.parent.mkdir(parents=True, exist_ok=True)
                run_id = str(uuid.uuid4())
                export_report(run_id, args.csv or 'unknown', detector, threshold, preset, windows, str(export_path))
                print(f'Exported report to {export_path}')
            elif choice == '6':
                hist_path = DATA_DIR / 'history.json'
                if not hist_path.exists():
                    print('No history file found.')
                else:
                    import json
                    with open(hist_path, 'r', encoding='utf-8') as f:
                        hist = json.load(f)
                    for entry in hist:
                        print(f"Run {entry.get('run_id')} – {entry.get('detector')} – {entry.get('window_count')} windows – {entry.get('timestamp')}")
            elif choice == '7' or choice.lower() == 'q' or choice.lower() == 'quit':
                print('Exiting HivePulse.')
                break
            else:
                print('Invalid choice.')
        return

    # One-shot mode with arguments
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
