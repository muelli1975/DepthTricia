@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Entpacken.ps1"
if errorlevel 1 pause
