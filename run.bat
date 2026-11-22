@echo off
cd /d "%~dp0"
python -m src.assembler examples\reference.asm build\reference.bin --test
if errorlevel 1 exit /b 1
python -m unittest discover -s tests -v
