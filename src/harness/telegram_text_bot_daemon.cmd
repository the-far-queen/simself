@echo off
REM telegram_text_bot_daemon.cmd — standalone bot launcher
REM Uses pythonw (no console window) so bot runs independently of any hermes session.
REM Logs to vault/40-scratch/telegram_text_bot.log

set PYTHONW=C:\Users\Admin\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe
set BOT_DIR=C:\Users\Admin\simself\src\harness
set LOG=C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_text_bot.log

REM detach so this .cmd can exit without ending the python process
start "far_queen_bot" /B "%PYTHONW%" "%BOT_DIR%\telegram_text_bot.py" >> "%LOG%" 2>&1

echo launched. PID will appear in %LOG%