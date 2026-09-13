"""
Telegram bot supervisor — keeps telegram_text_bot.py running no matter what.

Standalone process. Started by telegram_bot_supervisor.cmd.
Watches the bot process. If it ends for any reason, waits, then restarts.
Owns nothing. Logs to vault/40-scratch/telegram_supervisor.log.

This solves the multiprocess problem: hermes session ends -> bot ends.
But supervisor is independent of hermes (launched via pythonw from .cmd).
"""

import os
import sys
import time
import subprocess
from pathlib import Path

VAULT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax")
BOT_SCRIPT = Path(r"C:\Users\Admin\simself\src\harness\telegram_text_bot.py")
PYTHONW = Path(r"C:\Users\Admin\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe")
LOG = VAULT / "40-scratch" / "telegram_supervisor.log"
PID_FILE = VAULT / "40-scratch" / "telegram_supervisor.pid"
RESTART_DELAY_SEC = 5
MAX_RESTART_BACKOFF_SEC = 60


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def pid_alive(pid: int) -> bool:
    """Windows: check if process is alive without throwing on access-denied."""
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == STILL_ACTIVE
    except Exception:
        return False


def start_bot() -> subprocess.Popen:
    """Launch the bot via pythonw so it's standalone (no console, decoupled)."""
    log(f"starting bot: {PYTHONW} {BOT_SCRIPT}")
    return subprocess.Popen(
        [str(PYTHONW), str(BOT_SCRIPT)],
        cwd=str(BOT_SCRIPT.parent),
        creationflags=0x00000008,  # DETACHED_PROCESS
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


def main():
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    log(f"supervisor started, my_pid={os.getpid()}")
    backoff = RESTART_DELAY_SEC
    consecutive_failures = 0
    try:
        proc = start_bot()
        while True:
            try:
                ret = proc.wait(timeout=30)
                # bot ended on its own
                log(f"bot ended, exit code={ret}")
            except subprocess.TimeoutExpired:
                # bot still running, check it
                if proc.poll() is None:
                    # still alive, reset backoff
                    consecutive_failures = 0
                    backoff = RESTART_DELAY_SEC
                    time.sleep(10)
                    continue
                # already ended
                ret = proc.returncode
                log(f"bot ended, exit code={ret}")
            # restart with backoff
            consecutive_failures += 1
            backoff = min(RESTART_DELAY_SEC * (2 ** (consecutive_failures - 1)), MAX_RESTART_BACKOFF_SEC)
            log(f"restarting bot in {backoff}s (failure #{consecutive_failures})")
            time.sleep(backoff)
            proc = start_bot()
    except KeyboardInterrupt:
        log("supervisor interrupted")
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()