import sys
from pathlib import Path

# Import package modules
from epochledger.db import reset_db
from epochledger.experiment import (
    create_experiment,
    challenger_flow,
)
from epochledger.ui import generate_report


def main():
    # 1. Reset / initialise DB
    reset_db()
    # 2. Create a demo experiment
    exp_name = "demo_experiment"
    create_experiment(exp_name)
    # 3. Run a challenger flow (this will also promote to champion if none)
    verdict = challenger_flow(exp_name, "run_1")
    print(f"Verdict for first run: {verdict}")
    # 4. Run a second challenger to demonstrate comparison
    verdict2 = challenger_flow(exp_name, "run_2")
    print(f"Verdict for second run: {verdict2}")
    # 5. Generate static HTML report
    output_file = Path("static") / f"report_{exp_name}.html"
    generate_report(exp_name, output_file)
    print(f"Report generated at {output_file.resolve()}")
    # 6. Indicate demo success
    print("DONE task_ai_ml_02__v01_python_solo-founder_offline-first")
    return 0

if __name__ == "__main__":
    sys.exit(main())
