@echo off
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Error: Virtual environment not found. Please run 'python -m venv .venv' first.
    pause
    exit /b 1
)

echo Starting server...
python run.py