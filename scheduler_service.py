#!/usr/bin/env python3
"""
Mindrian Daily Summary Scheduler
================================

Background service for Render.com that sends daily summary emails.
Runs at configured hours (default: 6 AM and 6 PM UTC).

Usage:
    As Render Background Worker:
        Start command: python scheduler_service.py

    Local testing:
        python scheduler_service.py --test  (sends immediately, then exits)

Environment Variables:
    DAILY_SUMMARY_HOURS: Comma-separated hours to run (default: "6,18")
    DAILY_SUMMARY_RECIPIENT: Email recipient (default: jsagir@gmail.com)
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Ensure we're in project root
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
DEFAULT_HOURS = [6, 18]  # 6 AM and 6 PM UTC
RUN_HOURS = [int(h.strip()) for h in os.getenv("DAILY_SUMMARY_HOURS", "6,18").split(",")]
LOG_FILE = PROJECT_ROOT / "logs" / "scheduler.log"


def log(message: str):
    """Log message to console and file."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    # Also write to log file
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception:
        pass  # Don't fail if logging fails


def run_daily_summary() -> bool:
    """
    Execute the daily summary script.

    Returns:
        True if successful, False otherwise
    """
    log("Starting daily summary job...")

    script_path = PROJECT_ROOT / "scripts" / "daily_summary.py"

    if not script_path.exists():
        log(f"ERROR: Script not found: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--last-24h"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(PROJECT_ROOT)
        )

        # Log output
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                log(f"  {line}")

        if result.returncode == 0:
            log("Daily summary completed successfully")
            return True
        else:
            log(f"Daily summary failed with code {result.returncode}")
            if result.stderr:
                log(f"  Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        log("ERROR: Daily summary timed out after 5 minutes")
        return False
    except Exception as e:
        log(f"ERROR: Failed to run daily summary: {e}")
        return False


def run_scheduler():
    """
    Main scheduler loop.

    Runs continuously, checking every minute if it's time to send the daily summary.
    """
    log(f"Scheduler started. Will run at hours: {RUN_HOURS} UTC")
    log(f"Current UTC time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    last_run_date = None
    last_run_hour = None

    while True:
        now = datetime.utcnow()
        current_date = now.date()
        current_hour = now.hour

        # Check if we should run
        should_run = (
            current_hour in RUN_HOURS and
            (current_date != last_run_date or current_hour != last_run_hour)
        )

        if should_run:
            success = run_daily_summary()
            last_run_date = current_date
            last_run_hour = current_hour

            if success:
                log(f"Next run scheduled for hour {RUN_HOURS}")

        # Sleep for 60 seconds before checking again
        time.sleep(60)


def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Mindrian Daily Summary Scheduler")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run daily summary immediately and exit (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run daily summary in dry-run mode (no email sent)"
    )

    args = parser.parse_args()

    if args.test or args.dry_run:
        log("Running in test mode...")

        if args.dry_run:
            # Run with --dry-run flag
            script_path = PROJECT_ROOT / "scripts" / "daily_summary.py"
            result = subprocess.run(
                [sys.executable, str(script_path), "--dry-run"],
                cwd=str(PROJECT_ROOT)
            )
            sys.exit(result.returncode)
        else:
            # Run actual summary
            success = run_daily_summary()
            sys.exit(0 if success else 1)

    # Normal operation - run scheduler loop
    try:
        run_scheduler()
    except KeyboardInterrupt:
        log("Scheduler stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
