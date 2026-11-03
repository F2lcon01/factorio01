@echo off
rem Double-click: opens the Factorio language switcher (asks for administrator rights).
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Change-Language.ps1"
