@echo off
REM telegram_bot_supervisor.cmd — start the supervisor as a standalone process.
REM Supervisor watches the bot and restarts it on any exit.
REM Decouples from any hermes session. Use Windows Task Scheduler for boot-start.

set PYTHONW=C:\Users\Admin\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe
set SUPERVISOR=C:\Users\Admin\simself\src\harness\telegram_bot_supervisor.py
set LOG=C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_supervisor.log

start "far_queen_bot_supervisor" /B "%PYTHONW%" "%SUPERVISOR%" >> "%LOG%" 2>&1

echo supervisor launched. check %LOG% for status.
echo to verify: type C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_supervisor.pid
echo and confirm the pid is alive with tasklist /FI "PID eq <pid>".