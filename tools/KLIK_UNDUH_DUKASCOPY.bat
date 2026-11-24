@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo Unduh tick XAUUSD Dukascopy 2020 - kemarin. Kalau putus / laptop mati: klik ulang, lanjut sendiri.
python -I "%~dp0unduh_dukascopy.py" 2020-01
echo.
echo Cek hasil: "C:\scalping\DATA TICK\_DUKASCOPY\KEMAJUAN.txt"
pause
