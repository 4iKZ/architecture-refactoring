"""Create a small backdated git history inside this fixture.

Run once before the evaluation scenarios if you want change-frequency
evidence to be available to the agent.

The history deliberately shows churn in orders/billing while
notifier.py has not been touched since the initial import.
"""

import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def git(*args, date=None):
    env = os.environ.copy()
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    subprocess.run(
        ["git", *args],
        cwd=HERE,
        check=True,
        env=env,
        capture_output=True,
    )


def main():
    if (HERE / ".git").exists():
        print("history already exists for", HERE)
        return
    git("init", "-q")
    git("config", "user.name", "Fixture Bot")
    git("config", "user.email", "fixture@example.com")
    git("add", ".")
    git("commit", "-q", "-m", "initial import", date="2025-06-01T10:00:00")
    for fname, message, date in [
        ("shop/orders.py", "add discount rule", "2026-08-15T09:00:00"),
        ("shop/billing.py", "pass gateway fee to total", "2026-08-21T15:30:00"),
        ("shop/orders.py", "fix rounding", "2026-09-01T11:00:00"),
    ]:
        path = HERE / fname
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n# %s\n" % message)
        git("add", fname)
        git("commit", "-q", "-m", message, date=date)
    print("created backdated history for", HERE)


if __name__ == "__main__":
    main()
