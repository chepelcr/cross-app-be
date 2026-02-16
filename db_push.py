"""
Database push script — Python equivalent of `npm run db push`.

Usage:
    python3 db_push.py          # Auto-generate migration and apply it
    python3 db_push.py --only-migrate  # Only apply existing migrations (no autogenerate)
    python3 db_push.py --only-generate # Only generate migration (don't apply)
"""

import subprocess
import sys
from datetime import datetime


def run(cmd: list[str]) -> int:
    print(f">>> {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    only_migrate = "--only-migrate" in sys.argv
    only_generate = "--only-generate" in sys.argv

    # First upgrade to head if not only generating
    if not only_generate:
        print("\n=== Upgrading to latest migration ===\n")
        rc = run(["python3", "-m", "alembic", "upgrade", "head"])
        if rc != 0:
            print("WARNING: Upgrade failed, continuing with generation...")

    if not only_migrate:
        msg = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n=== Generating migration: {msg} ===\n")
        rc = run(["python3", "-m", "alembic", "revision", "--autogenerate", "-m", msg])
        if rc != 0:
            print("Migration generation failed!")
            sys.exit(rc)

    if not only_generate:
        print("\n=== Applying migrations (upgrade head) ===\n")
        rc = run(["python3", "-m", "alembic", "upgrade", "head"])
        if rc != 0:
            print("Migration apply failed!")
            sys.exit(rc)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
