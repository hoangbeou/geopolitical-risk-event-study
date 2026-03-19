"""
Main entrypoint: Event Study only.

All QQR / dependence / portfolio logic has been removed. Use the Event
Study runner as the single workflow focus.
"""

from pathlib import Path
import sys
import os

# Allow importing sibling modules when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Delegate to the Event Study runner."""
    try:
        from scripts.run_event_study import main as event_main
    except ImportError as exc:
        raise SystemExit(f"Không thể import scripts/run_event_study.py: {exc}")

    # Ensure outputs folder exists; data path kept for reference if needed
    Path("results").mkdir(exist_ok=True)
    return event_main()


if __name__ == "__main__":
    main()

