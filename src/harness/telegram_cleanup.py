"""
Telegram bot cleanup utility — drop stale inbox/outbox messages.

Use when:
- bot was down and inbox piled up with old inbound messages
- outbox has pending/reply files older than threshold with no live bot
- lockfile from a unresponsive process is left behind

Usage:
    python telegram_cleanup.py                # show what would be cleaned
    python telegram_cleanup.py --apply       # actually delete
    python telegram_cleanup.py --apply --older-than-hours 24
    python telegram_cleanup.py --unlock      # only clear stale lockfile

Safe: only deletes files older than --older-than-hours (default 24h).
"""

import argparse
import os
import sys
import time
from pathlib import Path

VAULT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax")
INBOX = VAULT / "40-scratch" / "inbox"
OUTBOX = VAULT / "40-scratch" / "outbox"
LOCK = VAULT / "40-scratch" / "telegram_text_bot.lock"

# Windows pid-alive check
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def pid_alive(pid: int) -> bool:
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == STILL_ACTIVE
    except Exception:
        return False


def file_age_hours(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / 3600


def find_stale_lock() -> dict | None:
    if not LOCK.exists():
        return None
    try:
        old_pid = int(LOCK.read_text().strip())
    except (ValueError, OSError):
        return {"path": LOCK, "pid": None, "alive": False, "age_h": file_age_hours(LOCK)}
    return {
        "path": LOCK,
        "pid": old_pid,
        "alive": pid_alive(old_pid),
        "age_h": file_age_hours(LOCK),
    }


def find_stale_files(directory: Path, older_than_h: float) -> list[Path]:
    if not directory.exists():
        return []
    stale = []
    for chat_dir in directory.iterdir():
        if not chat_dir.is_dir():
            continue
        for f in chat_dir.iterdir():
            if not f.is_file():
                continue
            if file_age_hours(f) >= older_than_h:
                stale.append(f)
    return stale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete")
    ap.add_argument("--older-than-hours", type=float, default=24.0,
                    help="only delete files older than this (default 24h)")
    ap.add_argument("--unlock", action="store_true", help="only clear stale lockfile")
    args = ap.parse_args()

    print(f"=== telegram_cleanup ===")
    print(f"vault:    {VAULT}")
    print(f"inbox:    {INBOX}")
    print(f"outbox:   {OUTBOX}")
    print(f"lock:     {LOCK}")
    print(f"threshold: older than {args.older_than_hours}h")
    print()

    # check lock
    lock = find_stale_lock()
    if lock:
        alive_str = "ALIVE" if lock["alive"] else "unresponsive"
        age_str = f"{lock['age_h']:.1f}h old"
        print(f"lockfile present: pid={lock['pid']} status={alive_str} age={age_str}")
        if not lock["alive"]:
            if args.apply or args.unlock:
                if LOCK.exists():
                    LOCK.unlink()
                print(f"  -> removed unresponsive lockfile")
            else:
                print(f"  -> would remove (pass --apply or --unlock)")
    else:
        print(f"lockfile: none (clean)")
    print()

    # check inbox/outbox
    in_stale = find_stale_files(INBOX, args.older_than_hours)
    out_stale = find_stale_files(OUTBOX, args.older_than_hours)

    print(f"stale inbox files ({len(in_stale)}):")
    for f in in_stale:
        print(f"  {f.relative_to(VAULT)}  ({file_age_hours(f):.1f}h)")
    print(f"stale outbox files ({len(out_stale)}):")
    for f in out_stale:
        print(f"  {f.relative_to(VAULT)}  ({file_age_hours(f):.1f}h)")

    if args.apply and not args.unlock:
        for f in in_stale + out_stale:
            f.unlink()
            print(f"  deleted: {f.relative_to(VAULT)}")
        print(f"\nDeleted {len(in_stale)} inbox + {len(out_stale)} outbox files")
    elif in_stale or out_stale:
        print(f"\npass --apply to delete")


if __name__ == "__main__":
    main()