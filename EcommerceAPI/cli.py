import argparse
import os
import subprocess
import sys
from pathlib import Path

MICROSERVICES_DIR = Path("tests")


"""
🎉 Usage
Run customers only:
python -m ssqaapitest --service customers

Run all microservices:
python -m ssqaapitest --all

Run performance:
python -m ssqaapitest --service customers --perf

With HTML report:
python -m ssqaapitest --service customers --html

And it works in CI:
script:
  - python -m ssqaapitest --service $SERVICE

"""


def list_microservices():
    return sorted(
        d.name
        for d in MICROSERVICES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )


def main():
    parser = argparse.ArgumentParser(description="Unified QA Test Runner")

    parser.add_argument(
        "--service",
        help="Run tests for a specific microservice.",
        choices=list_microservices(),
    )

    parser.add_argument(
        "--all", action="store_true", help="Run ALL microservices (matrix-auto)."
    )

    parser.add_argument("--perf", action="store_true", help="Run performance tests.")

    parser.add_argument("--html", action="store_true", help="Generate HTML report.")

    args = parser.parse_args()

    # -------------------------------------------------
    # Microservice selection / validation
    # -------------------------------------------------
    if args.service:
        test_path = f"tests/{args.service}"
    elif args.all:
        test_path = "tests"
    else:
        print("ERROR: You must specify --service or --all")
        sys.exit(1)

    # -------------------------------------------------
    # Dynamic env injection
    # -------------------------------------------------
    os.environ.setdefault("ENABLE_STRUCTURED_LOGS", "true")
    os.environ.setdefault("AUTO_HTML_REPORT", "true")

    if args.perf:
        os.environ["RUN_PERF"] = "true"

    # -------------------------------------------------
    # Build pytest command dynamically
    # -------------------------------------------------
    cmd = ["pytest", test_path, "-s", "--disable-warnings"]

    if args.html:
        cmd.append("--auto-html-report")

    if args.perf:
        cmd.append("-m")
        cmd.append("performance")

    print(">>> Running:", " ".join(cmd))

    sys.exit(subprocess.call(cmd))
